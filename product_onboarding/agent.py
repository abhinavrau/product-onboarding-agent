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

"""Demonstration of Travel AI Conceirge using Agent Development Kit"""

from google.adk.agents import Agent

from product_onboarding import prompt
from product_onboarding.sub_agents.kyc_check.agent import kyc_check
from product_onboarding.sub_agents.product_recommender.agent import (
    product_recommender_agent,
)
from product_onboarding.sub_agents.qualify_customer.agent import qualify_customer_agent

root_agent = Agent(
    model="gemini-2.0-flash-001",
    name="root_agent",
    description="A Payment Oboarding Agent using the services of multiple sub-agents",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[
        qualify_customer_agent,
        product_recommender_agent,
        kyc_check,
    ],
)
