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

"""Search agent. Searches for general information about {os.getenv("AGENT_COMPANY_NAME", "Clover")}"""

import json  # Added import for json
import logging
import os
from io import BytesIO
from typing import Dict, Optional

from google.adk.agents import Agent
from google.adk.models import (  # Content and Part come from google.genai.types
    LlmRequest,
    LlmResponse,
)
from google.adk.tools import ToolContext, load_artifacts

# PIL.Image is not strictly needed if docai handles bytes directly
from google.genai import types  # Import types for Content and Part

from product_onboarding.sub_agents.kyc_check import prompt
from product_onboarding.tools import docai  # Import the docai module
from product_onboarding.tools.salesforce import (
    get_opportunity_details,
    update_opportunity_stage,
    update_opportunity_with_comment,
)


def _load_file_from_context(
    tool_context: ToolContext,
) -> tuple[Optional[bytes], Optional[str]]:
    """Loads a file from callback_context.user_content and returns its bytes and mime_type."""
    if tool_context.user_content and tool_context.user_content.parts:
        # user_content is a single Content object, iterate through its parts
        for part in tool_context.user_content.parts:
            if (
                isinstance(part, types.Part)
                and part.inline_data
                and part.inline_data.data
            ):
                try:
                    file_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type
                    # Basic check for supported mime types
                    if mime_type in ["image/jpeg", "image/png", "application/pdf"]:
                        logging.info(
                            f"Found file part in user_content with mime_type: {mime_type}"
                        )
                        return file_bytes, mime_type
                    # else:
                    # logging.info(f"Part found in user_content with mime_type: {mime_type}, but not a target file type.")
                except Exception as e:
                    logging.error(
                        f"Error accessing inline_data from user_content part: {e}"
                    )
                    # Continue checking other parts
        logging.warning(
            "No suitable file part (image/pdf) found in callback_context.user_content.parts."
        )
        return None, None
    else:
        logging.warning("No user_content or parts found in callback_context.")
        return None, None


def check_fraud_drivers_license(query: str, tool_context: "ToolContext"):
    """Calls DocAI to verify document is not fradulent"""

    file_bytes, mime_type = _load_file_from_context(tool_context)

    if not file_bytes or not mime_type:
        logging.warning("No file data found in user content to process for fraud check.")
        # Potentially return an LlmResponse indicating failure or missing data
        return None

    processor_name_env = os.getenv("ID_PROOFING_PROCESSOR_FULLPATH")
    logging.debug(
        f"check_fraud_drivers_license::processor_name_env: {processor_name_env}"
    )

    if not processor_name_env:
        logging.error(
            "Error: Missing one or more environment variables for DocAI:"
            "ID_PROOFING_PROCESSOR_FULLPATH"
        )
        # Potentially return an LlmResponse indicating configuration error
        return None

    try:
        processed_document = docai.process_document(
            processor_name=processor_name_env,
            image_buffer=file_bytes,  # process_document expects bytes
            mime_type=mime_type,
        )

        # Check for specific fraud signals in the processed document entities
        fraud_detected = False
        fraud_details = []

        # Specific fraud signals to check based on user feedback
        target_fraud_signal_types = {
            "fraud_signals_is_identity_document": "PASS",  # Expected value for non-fraud
            "fraud_signals_image_manipulation": "PASS",  # Expected value if not manipulated (assuming "PASS" means clear)
        }

        if processed_document.entities:
            for entity in processed_document.entities:
                entity_type = entity.type_
                mention_text = entity.mention_text

                if entity_type == "fraud_signals_is_identity_document":
                    if mention_text != target_fraud_signal_types[entity_type]:
                        fraud_detected = True
                        fraud_details.append(
                            f"Identity Document Check Failed: {mention_text} (Expected {target_fraud_signal_types[entity_type]})"
                        )

                # elif entity_type == "fraud_signals_image_manipulation":
                #     # If this signal is present and not explicitly "PASS", consider it a flag.
                #     # The documentation isn't very specific on mention_text values for this,
                #     # but "PASS" usually indicates no issue.
                #     if mention_text != target_fraud_signal_types[entity_type]:
                #         fraud_detected = True
                #         fraud_details.append(
                #             f"Image Manipulation Detected: {mention_text} (Expected {target_fraud_signal_types[entity_type]})"
                #         )

        if fraud_detected:
            logging.info(f"Fraud signals detected: {'; '.join(fraud_details)}")
            fraud_message = f"Fraudulent document detected based on DocAI analysis. Details: {'; '.join(fraud_details)}"
            # update_opportunity_with_comment(callback_context, fraud_message) # Optional: update Salesforce
            return fraud_message

        else:
            return "No targeted fraud signals (identity document, image manipulation) detected by DocAI."

    except Exception as e:
        logging.error(f"Error calling Document AI: {e}")
        error_message = f"Error processing document with DocAI: {e}"
        # update_opportunity_with_comment(callback_context, error_message) # Optional: update Salesforce
        return error_message


def extract_info_from_drivers_license(query: str, tool_context: "ToolContext"):
    """Extracts Name and Address from a driver's license using Document AI."""
    file_bytes, mime_type = _load_file_from_context(tool_context)

    if not file_bytes or not mime_type:
        logging.warning("No file data found in user content for driver's license extraction.")
        return json.dumps(
            {"error": "No file provided for driver's license processing."}
        )

    processor_name_env = os.getenv("DL_PROCESSOR_FULLPATH")
    if not processor_name_env:
        logging.error("Error: Missing DL_PROCESSOR_FULLPATH environment variable.")
        return json.dumps(
            {"error": "Document AI processor for driver's license is not configured."}
        )

    try:
        processed_document = docai.process_document(
            processor_name=processor_name_env,
            image_buffer=file_bytes,
            mime_type=mime_type,
        )

        extracted_data: Dict[str, Optional[str]] = {"Names": None, "Address": None}
        given_names = []
        family_names = []

        if processed_document.entities:
            for entity in processed_document.entities:
                if entity.type_ == "Given Names":
                    given_names.append(entity.mention_text.strip())
                elif entity.type_ == "Family Name":
                    family_names.append(entity.mention_text.strip())
                elif entity.type_ == "Address":
                    extracted_data["Address"] = entity.mention_text.strip()

        # Combine names, handling cases where parts might be missing
        full_name_parts = [name for name in given_names + family_names if name]
        if full_name_parts:
            extracted_data["Names"] = " ".join(full_name_parts)

        if not extracted_data["Names"] and not extracted_data["Address"]:
            return json.dumps(
                {
                    "error": "Could not extract Names or Address from the driver's license."
                }
            )

        return json.dumps(extracted_data)

    except Exception as e:
        logging.error(f"Error calling Document AI for driver's license: {e}")
        return json.dumps(
            {"error": f"Error processing driver's license with Document AI: {str(e)}"}
        )


def extract_info_from_bank_statement(query: str, tool_context: "ToolContext"):
    """Extracts Name and Address from a bank statement using Document AI."""
    file_bytes, mime_type = _load_file_from_context(tool_context)

    if not file_bytes or not mime_type:
        logging.warning("No file data found in user content for bank statement extraction.")
        return json.dumps({"error": "No file provided for bank statement processing."})

    processor_name_env = os.getenv("BANK_STATEMENT_PROCESSOR_FULLPATH")
    if not processor_name_env:
        logging.error("Error: Missing BANK_STATEMENT_PROCESSOR_FULLPATH environment variable.")
        return json.dumps(
            {"error": "Document AI processor for bank statement is not configured."}
        )

    try:
        processed_document = docai.process_document(
            processor_name=processor_name_env,
            image_buffer=file_bytes,
            mime_type=mime_type,
        )

        extracted_data: Dict[str, Optional[str]] = {"Name": None, "Address": None}

        if processed_document.entities:
            for entity in processed_document.entities:
                if entity.type_ == "client_name":
                    extracted_data["Name"] = entity.mention_text.strip()
                elif entity.type_ == "client_address":
                    extracted_data["Address"] = entity.mention_text.strip()

        if not extracted_data["Name"] and not extracted_data["Address"]:
            return json.dumps(
                {"error": "Could not extract Name or Address from the bank statement."}
            )

        return json.dumps(extracted_data)

    except Exception as e:
        logging.error(f"Error calling Document AI for bank statement: {e}")
        return json.dumps(
            {"error": f"Error processing bank statement with Document AI: {str(e)}"}
        )


kyc_check = Agent(
    model="gemini-2.0-flash-001",
    name="kyc_check",
    description="""An agent that extracts the details of Drivers Licence and Bank Statement and verifies if the details match""",
    instruction=prompt.KYC_CHECK_AGENT_INSTR,
    tools=[
        load_artifacts,
        update_opportunity_with_comment,
        check_fraud_drivers_license,
        extract_info_from_drivers_license,
        extract_info_from_bank_statement,
    ],
)
