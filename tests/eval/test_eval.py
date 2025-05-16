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

"""Basic evaluation of the travel concierge agent."""

import pathlib

import dotenv
import pytest
from google.adk.evaluation import AgentEvaluator
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService

@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()


session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()

def test_acme():
    """Test the agent's basic flow with acme corp as company name"""
    AgentEvaluator.evaluate(
        agent_module="product_onboarding",
        eval_dataset_file_path_or_dir=str(pathlib.Path(__file__).parent / "data/"),
        num_runs=1,
    )
