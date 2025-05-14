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

import os

from google.adk.agents import Agent
from google.adk.tools import load_artifacts

from product_onboarding.tools.salesforce import (
    get_opportunity_details,
    update_opportunity_stage,
    update_opportunity_with_comment,
)
from product_onboarding.sub_agents.kyc_check import prompt

kyc_check = Agent(
    model="gemini-2.0-flash-001",
    name="kyc_check",
    description="""An agent that extracts the details of Drivers Licence and Bank Statement and verifies if the details match""",
    instruction=prompt.KYC_CHECK_AGENT_INSTR,
    tools=[load_artifacts, update_opportunity_with_comment],
)
