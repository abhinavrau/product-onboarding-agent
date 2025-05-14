import json
import os
from typing import Any, Dict, List, Union

import requests


# --- Helper Function: Get Photo URL ---
def get_photo_url(
    photos_data: List[Dict[str, Any]], api_key: str, max_width: int = 400
) -> str:
    """
    Constructs a photo URL from the first photo reference.
    """
    if (
        not photos_data
        or not isinstance(photos_data, list)
        or not photos_data[0].get("photo_reference")
    ):
        return ""
    photo_reference = photos_data[0]["photo_reference"]
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}"


# --- Modified Function: Get Place Details ---
def get_place_details(
    place_id: str, api_key: str
) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Fetches detailed information for a specific place using its place_id.
    """
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    fields = [
        "place_id",  # Ensure place_id is requested
        "name",
        "formatted_address",
        "geometry",
        "rating",
        "editorial_summary",
        "photo",
        "business_status",
    ]
    params = {"place_id": place_id, "key": api_key, "fields": ",".join(fields)}

    try:
        response = requests.get(details_url, params=params)
        response.raise_for_status()
        details_data = response.json()

        status = details_data.get("status")
        if status == "OK":
            return details_data.get("result", {})
        else:
            error_message = details_data.get(
                "error_message", f"Place Details API Error: {status}"
            )
            return {"error": error_message, "status": status}

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error fetching place details: {e}"}
    except Exception as e:
        return {
            "error": f"An unexpected error occurred during place details fetch: {e}"
        }


# --- Modified Function: Find Businesses From Text ---
def find_business_from_google_maps(
    query: str, max_results: int = 4
) -> Union[Dict[str, List[Dict[str, Any]]], Dict[str, str]]:
    """
    Fetches details for multiple businesses and formats them as specified.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_PLACES_API_KEY environment variable not set or empty."}

    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    search_params = {"query": query, "key": api_key, "fields": "place_id"}

    formatted_places_list = []

    try:
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()
        search_data = search_response.json()

        search_status = search_data.get("status")
        if search_status == "ZERO_RESULTS":
            return {"places": []}
        elif search_status != "OK":
            error_message = search_data.get(
                "error_message", f"Text Search API Error: {search_status}"
            )
            return {"error": error_message, "status": search_status}

        place_ids_from_search = [
            place.get("place_id")
            for place in search_data.get("results", [])
            if place.get("place_id")
        ]

        for p_id in place_ids_from_search[
            :max_results
        ]:  # Use p_id to avoid conflict with details['place_id']
            details = get_place_details(p_id, api_key)
            if "error" not in details:
                lat = details.get("geometry", {}).get("location", {}).get("lat")
                lng = details.get("geometry", {}).get("location", {}).get("lng")

                highlights = ""
                if details.get("editorial_summary") and isinstance(
                    details["editorial_summary"], dict
                ):
                    highlights = details["editorial_summary"].get("overview", "")

                image_url = get_photo_url(details.get("photos", []), api_key)

                actual_place_id = details.get(
                    "place_id", ""
                )  # Get the actual place_id from details
                map_url = (
                    f"https://www.google.com/maps/place/?q=place_id:{actual_place_id}"
                    if actual_place_id
                    else ""
                )

                formatted_place = {
                    "place_name": details.get("name", ""),
                    "address": details.get("formatted_address", ""),
                    "lat": str(lat) if lat is not None else "",
                    "long": str(lng) if lng is not None else "",
                    "review_ratings": details.get("rating", 0.0),
                    "highlights": highlights,
                    "image_url": image_url,
                    "map_url": map_url,  # Populated map_url
                    "place_id": actual_place_id,  # Populated place_id
                }
                formatted_places_list.append(formatted_place)
            else:
                print(
                    f"Warning: Could not get details for place_id {p_id}: {details.get('error')}"
                )

        return {"places": formatted_places_list}

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error during business search: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred during business search: {e}"}


# --- Main Execution Block ---
# if __name__ == "__main__":
#     business_query = "Not Just Coffee in Charlotte NC"
#     print(f"Searching for: '{business_query}'...")

#     result_data = find_businesses_from_text(business_query)

#     print(json.dumps(result_data, indent=2))
