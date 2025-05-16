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

"""Tests for the knowledgebase_search_agent tool."""

import logging
import os
import unittest

import pytest
from dotenv import load_dotenv
from google.adk.agents.invocation_context import InvocationContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext

# Assuming root_agent might be needed for context, adjust if not.
from product_onboarding.agent import root_agent
from product_onboarding.sub_agents.product_recommender.agent import (
    knowledgebase_search_agent,
)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()


session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()


class TestKnowledgebaseSearch(unittest.TestCase):
    """Test cases for the knowledgebase_search_agent tool."""

    def setUp(self):
        """Set up for test methods."""
        super().setUp()
        self.session = session_service.create_session(
            app_name="Product_Onboarding_Knowledgebase_Test",
            user_id="kb_tester01",
        )
        self.user_id = "kb_tester01"
        self.session_id = self.session.id

        self.invoc_context = InvocationContext(
            session_service=session_service,
            artifact_service=artifact_service, # Added artifact_service
            invocation_id="KnowledgebaseSearchTest",
            agent=root_agent,
            session=self.session,
        )
        self.tool_context = ToolContext(invocation_context=self.invoc_context)

        # Check for required environment variables
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("VERTEX_AI_SEARCH_LOCATION")
        self.engine_id = os.getenv("VERTEX_AI_SEARCH_ENGINE_ID")

        if not all([self.project_id, self.location, self.engine_id]):
            self.skipTest(
                "Required environment variables (GOOGLE_CLOUD_PROJECT, "
                "VERTEX_AI_SEARCH_LOCATION, VERTEX_AI_SEARCH_ENGINE_ID) are not set. "
                "Skipping integration test."
            )

    def test_knowledgebase_search_valid_query(self):
        """Tests knowledgebase_search_agent with a valid query."""
        query = "What are the available POS systems?"
        
        try:
            result = knowledgebase_search_agent(query=query, tool_context=self.tool_context)
            logging.info(f"Knowledgebase Search Result for query '{query}':")
            logging.info(f"  Answer Text: {result.get('answerText')}")
            logging.info(f"  References found: {len(result.get('references', []))}")
            # logging.info(f"Full result: {result}") # Optionally log the full result too

            self.assertIsNotNone(result, "The result should not be None.")
            self.assertIsInstance(result, dict, "The result should be a dictionary.")

            self.assertIn("answerText", result, "Result should contain 'answerText' key.")
            self.assertIn("references", result, "Result should contain 'references' key.")

            self.assertIsInstance(
                result["answerText"], (str, type(None)), "answerText should be a string or None."
            ) # API might return null if no answer
            self.assertIsInstance(result["references"], list, "references should be a list.")

            if result["references"]:
                for ref in result["references"]:
                    self.assertIsInstance(ref, dict, "Each reference should be a dictionary.")
                    self.assertIn("uri", ref, "Each reference should have a 'uri' key.")
                    self.assertIn("title", ref, "Each reference should have a 'title' key.")
            
            # Further check if artifact saving logic was triggered (if applicable and testable)
            # For now, we are primarily testing the search call and response structure.

        except Exception as e:
            self.fail(
                f"knowledgebase_search_agent raised an exception for query '{query}': {e}"
            )

    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
