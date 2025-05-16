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

"""Tests for DocAI tools."""

import json
import logging
import os
import unittest

import pytest
from dotenv import load_dotenv
from google.adk.agents.invocation_context import InvocationContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.cloud import (
    documentai,
)  # Required for DocAI client, though not directly used in these tests, it's good practice if process_document was used.
from google.genai import types as genai_types

# Assuming root_agent might be needed for context, adjust if not.
from product_onboarding.agent import root_agent
from product_onboarding.sub_agents.kyc_check.agent import (
    check_fraud_drivers_license,
    extract_info_from_bank_statement,
    extract_info_from_drivers_license,
)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()


session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()


class TestDocAITools(unittest.TestCase):
    """Test cases for the Document AI tools."""

    def setUp(self):
        """Set up for test methods."""
        super().setUp()
        self.session = session_service.create_session(
            app_name="Product_Onboarding_DocAI_Test",  # More specific app_name
            user_id="docai_tester01",
        )
        self.user_id = "docai_tester01"
        self.session_id = self.session.id

        # Basic InvocationContext, specific tests will create their own with user_content
        self.invoc_context = InvocationContext(
            session_service=session_service,
            invocation_id="DocAIBase",
            agent=root_agent,  # Or a more specific agent if applicable
            session=self.session,
        )
        self.tool_context = ToolContext(invocation_context=self.invoc_context)

    def test_check_fraud_drivers_license_integration(self):
        """Tests the check_fraud_drivers_license function by calling the actual DocAI service."""

        processor_name_env = os.getenv("ID_PROOFING_PROCESSOR_FULLPATH")

        self.assertIsNotNone(
            processor_name_env, "ID_PROOFING_PROCESSOR_FULLPATH env var not set."
        )
        if not processor_name_env:  # For type checker
            return

        file_path = "tests/data/DL-brenda-sample.jpeg"
        mime_type = "image/jpeg"

        self.assertTrue(os.path.exists(file_path), f"Test file not found: {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        mock_user_content = genai_types.Content(
            parts=[
                genai_types.Part(
                    inline_data=genai_types.Blob(data=file_bytes, mime_type=mime_type)
                )
            ]
        )
        invoc_context_with_file = InvocationContext(
            session_service=session_service,
            invocation_id="test_fraud_check_dl",
            agent=root_agent,
            session=self.session,
            user_content=mock_user_content,
        )
        tool_context_with_file = ToolContext(invocation_context=invoc_context_with_file)

        try:
            result_message = check_fraud_drivers_license(
                query="Check for fraud in driver's license",
                tool_context=tool_context_with_file,
            )

            self.assertIsNotNone(
                result_message, "The result message should not be None."
            )
            assert isinstance(result_message, str)
            logging.info(f"Fraud Check Result for {file_path}: {result_message}")

            expected_message_fragment = "No targeted fraud signals (identity document, image manipulation) detected by DocAI."
            self.assertIn(
                expected_message_fragment,
                result_message,
                f"Expected message for a valid DL not found. Got: {result_message}",
            )

        except Exception as e:
            self.fail(
                f"check_fraud_drivers_license raised an exception for {file_path}: {e}"
            )

    def test_extract_info_from_drivers_license_integration(self):
        """Tests extract_info_from_drivers_license by calling the actual DocAI service."""

        processor_name_env = os.getenv("DL_PROCESSOR_FULLPATH")
        self.assertIsNotNone(
            processor_name_env,
            "DL_PROCESSOR_FULLPATH env var not set. Skipping test.",
        )
        if not processor_name_env:
            return

        file_path = "tests/data/DL-brenda-sample.jpeg"
        mime_type = "image/jpeg"

        self.assertTrue(os.path.exists(file_path), f"Test file not found: {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        mock_user_content = genai_types.Content(
            parts=[
                genai_types.Part(
                    inline_data=genai_types.Blob(data=file_bytes, mime_type=mime_type)
                )
            ]
        )
        invoc_context_with_file = InvocationContext(
            session_service=session_service,
            invocation_id="test_dl_extract",
            agent=root_agent,
            session=self.session,
            user_content=mock_user_content,
        )
        tool_context_with_file = ToolContext(invocation_context=invoc_context_with_file)

        result_json = extract_info_from_drivers_license(
            "extract DL info", tool_context_with_file
        )
        self.assertIsNotNone(result_json, "Result JSON should not be None")
        result = json.loads(result_json)

        logging.info(f"Driver's License Extraction Result: {result}")

        self.assertNotIn(
            "error", result, f"API call failed with error: {result.get('error')}"
        )
        self.assertIn("Names", result, "Result should contain 'Names' key")
        self.assertIn("Address", result, "Result should contain 'Address' key")
        self.assertEqual(result.get("Names"), "BRENDA SAMPLE")
        self.assertEqual(result.get("Address"), "123 MAIN STREET\nHELENA, MT 59601")

    def test_extract_info_from_bank_statement_integration(self):
        """Tests extract_info_from_bank_statement by calling the actual DocAI service."""
        processor_name_env = os.getenv("BANK_STATEMENT_PROCESSOR_FULLPATH")
        self.assertIsNotNone(
            processor_name_env,
            "BANK_STATEMENT_PROCESSOR_FULLPATH env var not set. Skipping test.",
        )
        if not processor_name_env:
            return

        file_path = "tests/data/Bank-Statement-brenda-sample.pdf"
        mime_type = "application/pdf"

        self.assertTrue(os.path.exists(file_path), f"Test file not found: {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        mock_user_content = genai_types.Content(
            parts=[
                genai_types.Part(
                    inline_data=genai_types.Blob(data=file_bytes, mime_type=mime_type)
                )
            ]
        )
        invoc_context_with_file = InvocationContext(
            session_service=session_service,
            invocation_id="test_bs_extract",
            agent=root_agent,
            session=self.session,
            user_content=mock_user_content,
        )
        tool_context_with_file = ToolContext(invocation_context=invoc_context_with_file)

        result_json = extract_info_from_bank_statement(
            "extract bank statement info", tool_context_with_file
        )
        self.assertIsNotNone(result_json, "Result JSON should not be None")
        result = json.loads(result_json)

        logging.info(f"Bank Statement Extraction Result: {result}")

        self.assertNotIn(
            "error", result, f"API call failed with error: {result.get('error')}"
        )
        self.assertIn("Name", result, "Result should contain 'Name' key")
        self.assertIn("Address", result, "Result should contain 'Address' key")
        self.assertEqual(result.get("Name"), "Brenda Sample")
        self.assertEqual(result.get("Address"), "123 Main Street\nHelena, MT 59601")
