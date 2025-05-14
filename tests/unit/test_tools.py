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

"""Basic tests for individual tools."""

import unittest

import pytest
from dotenv import load_dotenv
from google.adk.agents.invocation_context import InvocationContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext

from product_onboarding.agent import root_agent
from product_onboarding.tools.places import find_business_from_google_maps


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()


session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()


class TestAgents(unittest.TestCase):
    """Test cases for the Travel Concierge cohort of agents."""

    def setUp(self):
        """Set up for test methods."""
        super().setUp()
        self.session = session_service.create_session(
            app_name="Travel_Concierge",
            user_id="traveler0115",
        )
        self.user_id = "traveler0115"
        self.session_id = self.session.id

        self.invoc_context = InvocationContext(
            session_service=session_service,
            invocation_id="ABCD",
            agent=root_agent,
            session=self.session,
        )
        self.tool_context = ToolContext(invocation_context=self.invoc_context)

    def test_places(self):
        result = find_business_from_google_maps("Not Just Coffee in Charlotte NC")
        print(result)
        self.assertNotIn("error", result, f"API call failed with error: {result.get('error')}")
        self.assertIn("places", result, "The result dictionary should contain a 'places' key.")
        
        places_list = result.get("places", [])
        self.assertTrue(any(place.get("place_id") == "ChIJ1Zy0mXCfVogRPyLjCWScplA" for place in places_list),
                        "The expected place_id ChIJ1Zy0mXCfVogRPyLjCWScplA was not found in the results.")
