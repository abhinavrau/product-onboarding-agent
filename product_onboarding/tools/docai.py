from google.cloud import documentai
import base64
import logging
def process_document(processor_name: str, image_buffer: bytes, mime_type: str) -> documentai.Document:
    """
    Process a document using the DocumentAI API.
    Args:
        processor_name: The Document AI processor name
        image_buffer: A buffer containing the image data
        mime_type: Mime type of the input image
    Returns:
        The parsed document
    """

    logging.info(f"Processing document with processor: {processor_name}")
    client = documentai.DocumentProcessorServiceClient()

    # Base64 encode buffer
    encoded_content = base64.b64encode(image_buffer).decode("utf-8")

    raw_document = documentai.RawDocument(
        content=encoded_content, mime_type=mime_type
    )

    request = documentai.ProcessRequest(
        name=processor_name,
        raw_document=raw_document,
        skip_human_review=True,
    )

    result = client.process_document(request=request)
    document = result.document

    return document
