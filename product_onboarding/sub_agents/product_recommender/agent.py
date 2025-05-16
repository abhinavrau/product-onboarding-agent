# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Validate Business agent. Finds and verifies a business using name and location"""
import base64
import logging
import os
from io import BytesIO
from typing import Optional

import PIL.Image
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.genai import Client, types

from product_onboarding.sub_agents.product_recommender import prompt, vaisearch
from product_onboarding.tools.salesforce import (
    get_opportunity_details,
    update_opportunity_stage,
    update_opportunity_with_comment,
)
from product_onboarding.tools.search import google_search_grounding

# Only Vertex AI supports image generation for now.
client = Client()


def _load_image_from_user_content(
    tool_context: "ToolContext",
) -> tuple[Optional[PIL.Image.Image], Optional[types.Part]]:
    """Loads the image from user_content field in tool.context and returns a PIL Image object and the image part."""
    if tool_context.user_content and tool_context.user_content.parts:
        # Assuming user_content.parts[0] is text and user_content.parts[1] is the image.
        # A more robust implementation would iterate parts and check mime_type.
        if len(tool_context.user_content.parts) > 1:
            image_part = tool_context.user_content.parts[1]
            # Check if the part has inline data, which is expected for an image from user_content
            if image_part and image_part.inline_data and image_part.inline_data.data:
                try:
                    image_bytes = image_part.inline_data.data
                    image = PIL.Image.open(BytesIO(image_bytes))
                    return image, image_part
                except Exception as e:
                    logging.error(f"Error opening image from inline_data: {e}")
                    return None, None
            else:
                logging.warning(
                    "Image part at index 1 is missing, does not contain inline data, or data is empty."
                )
                return None, None
        else:
            logging.warning(
                "No image part found at index 1 in user_content.parts (not enough parts)."
            )
            return None, None
    else:
        logging.warning("No user_content or parts found in tool_context.")
        return None, None


def image_editor(prompt: str, tool_context: "ToolContext"):
    """Generates an image based on the prompt using Gemini Flash 2.0 Image generation model."""
    # Get the directory of the current script
    # script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the image
    # image_path = os.path.join(script_dir, "input_image.jpeg")

    # Now open the image using the absolute path
    # image = PIL.Image.open(image_path)

    # Laod the image user upload earlier
    image_part = tool_context.load_artifact(filename="user:user_pos_image.png")

    if not image_part or not image_part.inline_data or not image_part.inline_data.data:
        logging.error(
            "Error: Could not load image artifact 'user:user_pos_image.png' or it"
            " has no data."
        )
        return {
            "status": "error",
            "detail": (
                "Failed to load image artifact 'user:user_pos_image.png' or artifact"
                " data is missing."
            ),
        }

    image_bytes = image_part.inline_data.data
    try:
        image_loaded = PIL.Image.open(BytesIO(image_bytes))
    except Exception as e:
        logging.error(f"Error opening image from artifact: {e}")
        return {
            "status": "error",
            "detail": f"Error processing image artifact: {e}",
        }

    if image_loaded is None:
        # This case might be less likely if PIL.Image.open raises an exception for bad data,
        # but it's a good fallback.
        logging.error("Error: Image data from artifact could not be opened by PIL.")
        return {
            "status": "error",
            "detail": "Image data from artifact is invalid or corrupted.",
        }

    logging.info("Loaded image:")
    # Generate new image
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[prompt, image_loaded],  # Use the loaded artifact image
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    if response.candidates:
        candidate = response.candidates[0]
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.text is not None:
                    logging.info(part.text)
                elif part.inline_data is not None and part.inline_data.data is not None:
                    # Save the new image
                    tool_context.save_artifact(
                        "user:pos_in_store_image.png",
                        types.Part.from_bytes(
                            data=part.inline_data.data, mime_type="image/png"
                        ),
                    )
                elif part.inline_data is not None and part.inline_data.data is None:
                    logging.warning(
                        "part.inline_data.data is None, skipping artifact save."
                    )
        else:
            logging.warning("No content or parts found in the candidate.")
    else:
        logging.warning("No candidates found in the response.")
    return {
        "status": "success",
        "detail": "Image generated successfully and stored in artifacts.",
        "filename": "pos_in_store_image.png",
    }


def identify_pos_model(prompt: str, tool_context: "ToolContext"):
    # Get the directory of the current script
    # script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the image
    # image_path = os.path.join(script_dir, "input_image.jpeg")

    # Now open the image using the absolute path
    # image = PIL.Image.open(image_path)

    image_loaded, image_part = _load_image_from_user_content(tool_context)
    if image_loaded is None:
        return {
            "status": "error",
            "detail": "No image artifact found to process.",
        }

    # create an image from
    logging.info("Loaded image")
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=[
            """You are an expert in identifying the make and model of a Point of Sale systems in a image. Identify the Point of Sale (POS) make and model in the image.
            If the image is not POS model then do not attempt to idenify it. 
            """,
            image_loaded,
        ],
    )
    # save the image to artifacts so it can be looked up later
    if image_part and image_part.inline_data and image_part.inline_data.data and image_part.inline_data.mime_type:
        tool_context.save_artifact(
            "user:user_pos_image.png",
            types.Part.from_bytes(
                data=image_part.inline_data.data, mime_type=image_part.inline_data.mime_type
            ),
        )
    return response.text


def knowledgebase_search_agent(query: str, tool_context: "ToolContext"):
    # get the GOOGLE_CLOUD_PROJECT from .env
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_AI_SEARCH_LOCATION")
    engine_id = os.getenv("VERTEX_AI_SEARCH_ENGINE_ID")

    if not project_id:
        logging.error("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
        return {
            "answerText": (
                "Configuration error: The GOOGLE_CLOUD_PROJECT environment variable is"
                " not set. Please configure it to proceed with knowledgebase search."
            ),
            "references": [],
        }
    if not location:
        logging.error("Error: VERTEX_AI_SEARCH_LOCATION environment variable not set.")
        return {
            "answerText": (
                "Configuration error: The VERTEX_AI_SEARCH_LOCATION environment"
                " variable is not set. Please configure it to proceed with"
                " knowledgebase search."
            ),
            "references": [],
        }
    if not engine_id:
        logging.error("Error: VERTEX_AI_SEARCH_ENGINE_ID environment variable not set.")
        return {
            "answerText": (
                "Configuration error: The VERTEX_AI_SEARCH_ENGINE_ID environment"
                " variable is not set. Please configure it to proceed with"
                " knowledgebase search."
            ),
            "references": [],
        }

    # vaisearch.vertex_ai_search now returns a dictionary like:
    # {
    #     "answerText": str,
    #     "references": list[{"uri": str, "title": str}],
    #     "blobAttachments": list[{"data": {"mimeType": str, "data": str}}] # data is base64
    # }
    api_response = vaisearch.vertex_ai_search(project_id, location, engine_id, query)

    if (
        api_response
        and "blobAttachments" in api_response
        and isinstance(api_response["blobAttachments"], list)
    ):
        for index, attachment in enumerate(api_response["blobAttachments"]):
            if (
                not isinstance(attachment, dict)
                or "data" not in attachment
                or not isinstance(attachment["data"], dict)
            ):
                continue

            mime_type = attachment["data"].get("mimeType")
            base64_image_data = attachment["data"].get("data")

            if base64_image_data and mime_type:
                try:
                    image_bytes = base64.b64decode(base64_image_data)

                    # Define a unique artifact filename
                    extension = "png"  # Default extension
                    if mime_type == "image/jpeg":
                        extension = "jpg"
                    elif mime_type == "image/png":
                        extension = "png"
                    elif mime_type == "image/gif":
                        extension = "gif"
                    elif "/" in mime_type and mime_type.startswith(
                        "image/"
                    ):  # Fallback for other image/* types
                        derived_extension = mime_type.split("/")[-1]
                        if derived_extension:  # Ensure it's not empty
                            extension = derived_extension

                    artifact_filename = f"user:search_result_image_{index}.{extension}"

                    # Create a genai.types.Part from bytes
                    image_artifact = types.Part.from_bytes(
                        data=image_bytes, mime_type=mime_type
                    )

                    # Save the artifact using tool_context
                    tool_context.save_artifact(artifact_filename, image_artifact)

                    # Add the artifact filename to the attachment for later reference
                    attachment["artifact_filename"] = artifact_filename

                    # Remove the original base64 data and mime_type from the attachment's data dict
                    # to avoid sending large data back to the LLM if only reference is needed.
                    del attachment["data"]["data"]
                    if (
                        "mimeType" in attachment["data"]
                    ):  # It should be there, but good to check
                        del attachment["data"]["mimeType"]

                except Exception as e:
                    # Log the error but continue processing other items
                    logging.error(
                        f"Error processing/saving search result image artifact from blobAttachment at index {index} for query '{query}': {e}"
                    )
            elif not base64_image_data:
                logging.warning(
                    f"No base64 data found in blobAttachment at index {index} for query '{query}'"
                )
            elif not mime_type:
                logging.warning(
                    f"No mimeType found in blobAttachment at index {index} for query '{query}'"
                )

    # Return only answerText and references as per feedback
    return {
        "answerText": api_response.get("answerText"),
        "references": api_response.get("references", []),  # Default to empty list
    }


def after_agent_callback(callback_context: ToolContext):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the image
    image_path = os.path.join("file://", script_dir, "handheld_terminal_image.png")

    image_artifact = types.Part.from_uri(file_uri=image_path, mime_type="image/png")
    callback_context.save_artifact(
        "handheld_terminal_image.png", artifact=image_artifact
    )


""" 
image_editor_agent = Agent(
    model="gemini-2.0-flash-001",
    name="image_editor_agent",
    description="An agent that edits images.",
    instruction="You are an agent whose job is to replace the POS system in the image with the recommended one.",
    tools=[generate_image_flash],
) """

""" identify_pos_model = Agent(
    model="gemini-2.0-flash-001",
    name="identify_pos_model",
    description="An agent that identifies the POS model in the images.",
    instruction="Given an image call the `identify_pos_model_flash` tool to identify the Point of Sale Terminal make and model.",
    tools=[identify_pos_model_flash, load_artifacts],
) """


search_agent = Agent(
    # model="gemini-2.0-flash",
    model="gemini-2.5-flash-preview-04-17",
    name="search_agent",
    description=f"""Searches for general information about {os.getenv("AGENT_COMPANY_NAME", "ACME Corp")}""",
    instruction=prompt.SEARCH_AGENT_INSTR,
    tools=[google_search_grounding],
)


product_recommender_agent = Agent(
    model="gemini-2.5-flash-preview-04-17",
    name="product_recommender_agent",
    description="A agent who recommends a POS solution based on the needs of the business owner",
    instruction=prompt.PRODUCT_RECOMENDER_AGENT_INSTR,
    tools=[
        knowledgebase_search_agent,
        AgentTool(agent=search_agent),
        identify_pos_model,
        image_editor,
        get_opportunity_details,
        update_opportunity_with_comment,
        update_opportunity_stage,
    ],
)
