import base64  # Kept for now, may not be strictly needed

from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions

# TODO(developer): Uncomment these variables before running the sample.
# project_id = "YOUR_PROJECT_ID"
# location = "YOUR_LOCATION"          # Values: "global", "us", "eu"
# engine_id = "YOUR_APP_ID" # This is often referred to as Data Store ID in the context of Answer API
# search_query = "YOUR_SEARCH_QUERY"

"""Calls the Vertex AI Search API to get an answer for the query."""


def vertex_ai_search(
    project_id: str,
    location: str,
    engine_id: str,  # For Answer API, this is typically the Data Store ID
    search_query: str,
) -> dict:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.ConversationalSearchServiceClient(
        client_options=client_options
    )  # Answer method is part of SearchServiceClient

    # The full resource name of the search app serving config or data store
    # For Answer API, this is typically the data store.
    # Example: projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{engine_id}
    # However, the 'answer' method uses a serving_config like search.
    # Let's assume engine_id is the engine_id for a serving_config.
    serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

    answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(
        ignore_adversarial_query=False,  # Optional: Ignore adversarial query
        ignore_non_answer_seeking_query=False,  # Optional: Ignore non-answer seeking query
        ignore_low_relevant_content=False,  # Optional: Return fallback answer when content is not relevant
        model_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(
            model_version="stable",
        ),
        prompt_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(
            preamble="""Given the conversation between a user and a helpful assistant and some search results, create a final answer for the assistant. 
                    The answer should use all relevant information from the search results, not introduce any additional information, and use exactly the same words as the search results when possible. 
                    The assistant's answer should be no more than 20 sentences. The assistant's answer should be formatted as a bulleted list. 
                    Each list item should start with the '- ' symbol."""
        ),
        include_citations=True,  # Optional: Include citations in the response
        answer_language_code="en",
        # multimodal_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.MultimodalSpec(
        #     imageSource="CORPUS_IMAGE_ONLY",
        # ),
    )

    query_understanding_spec = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec(
        query_rephraser_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(
            disable=False,  # Optional: Disable query rephraser
            max_rephrase_steps=1,  # Optional: Number of rephrase steps
        ),
        # Optional: Classify query types
        query_classification_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec(
            types=[
                discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.ADVERSARIAL_QUERY,
                discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.NON_ANSWER_SEEKING_QUERY,
            ]  # Options: ADVERSARIAL_QUERY, NON_ANSWER_SEEKING_QUERY or both
        ),
    )
    # Construct the AnswerRequest
    request = discoveryengine.AnswerQueryRequest(
        serving_config=serving_config,
        query=discoveryengine.Query(text=search_query),
        answer_generation_spec=answer_generation_spec,
        session=None,  # Optional: include previous session ID to continue a conversation
        query_understanding_spec=query_understanding_spec,
        search_spec=discoveryengine.AnswerQueryRequest.SearchSpec(
            search_params=discoveryengine.AnswerQueryRequest.SearchSpec.SearchParams(
                max_return_results=3
            )
        ),
    )

    # Call the answer API
    response = client.answer_query(request)

    # Process the response
    answer_text = response.answer.answer_text

    references_list = []
    if hasattr(response.answer, "references") and response.answer.references:
        for ref in response.answer.references:
            if ref.chunk_info and ref.chunk_info.document_metadata:
                uri = ref.chunk_info.document_metadata.uri
                # replace gs:// with https://storage.googleapis.com/
                uri = uri.replace("gs://", "https://storage.cloud.google.com/")
                title = ref.chunk_info.document_metadata.title
                references_list.append({"uri": uri, "title": title})

    attachments_list = []
    if (
        hasattr(response.answer, "blob_attachments")
        and response.answer.blob_attachments
    ):
        for attachment in response.answer.blob_attachments:
            if attachment.data:
                attachments_list.append(
                    {
                        "data": {  # Matching the example response structure
                            "mimeType": attachment.data.mime_type,
                            "data": attachment.data.data,  # Assuming this is already a base64 encoded string
                        }
                    }
                )

    return {
        "answerText": answer_text,
        "references": references_list,
        "blobAttachments": attachments_list,
    }
