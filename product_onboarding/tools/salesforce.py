from typing import Any, Dict, List

from google.adk.tools import ToolContext




def update_opportunity_with_comment(
    business_name: str,
    comment_text: str,
    tool_context: "ToolContext",
) -> dict:

    return {
        "status": "success",
        "message": f"Comment added successfully to opportunity '{business_name}'.",
    }


def update_opportunity_stage(
    business_name: str,
    new_stage: str,
    tool_context: "ToolContext",
) -> dict:
    return {
        "status": "success",
        "message": f"Opportunity with '{business_name}' stage updated successfully to '{new_stage}'.",
    }


def get_opportunity_details(
    business_name: str,
    tool_context: "ToolContext",
) -> dict:

    return {
        "status": "success",
        "message": f"Opportunity found for customer '{business_name}'.",
        "opportunity_id": 1,
    }

