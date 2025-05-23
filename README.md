# Product Onboarding Agent

Demo Sales agent for a Point of Sales (POS) company using the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/). Heavily inspired by the the [ADK-Samples](https://github.com/google/adk-samples).

## Goals
- Showcase the art of the possible of an AI agent helping a small business owner select a Point of Sale system using multimodal capability.
  
![](vision.png)

## Agent Design
![](agent-design.png)
## Prerequisites

*   Authenticated Google Cloud Account with the following services enabled
    *   [Gemini API](https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com) or [Google AI Studio](https://aistudio.google.com/) API Key - to access Gemini models
    *   [Places API](https://console.cloud.google.com/apis/library/places-backend.googleapis.com) - Used to verify business
    *   [Discovery Engine](https://console.cloud.google.com/apis/library/discoveryengine.googleapis.com) (a.k.a. Vertex AI Search) - Knowledgebase Search Engine
    *   [Cloud Storage](https://console.cloud.google.com/apis/library/storage.googleapis.com) - to store Knowledgebase documents
    *   [Document AI](https://console.cloud.google.com/apis/library/documentai.googleapis.com) - To detect verify Identity documents and extract info from Identity documents.

*   Python 3.11 or higher
*   [Poetry](https://python-poetry.org/docs/#installation) installed

## Setup Instructions

1.  **Clone the repository:**
    If you haven't already, clone the repository to your local machine:
    ```bash
    git clone https://github.com/abhinavrau/product-onboarding-agent.git 
    cd product-onboarding
    ```

2.  **Create Virtual Environment and install dependencies using Poetry:**
    Navigate to the project's root directory (`product-onboarding`) in your terminal and run:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    poetry install
    ```
    This command will create a virtual environment and install all the dependencies specified in `pyproject.toml`.

    **Note on Keyring Errors:** If you encounter a `RuntimeError` related to `keyring` during `poetry install` or `poetry update`, you might need to set the `PYTHON_KEYRING_BACKEND` environment variable. Try running the command as follows:
    ```bash
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring poetry install
    ```
    or for updates:
    ```bash
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring poetry update
    ```
3. **Create a AI Search Application in GCP for KnowledgeBase search**
  
  * In the GCP Console search for `AI Applications` --> `Create App`
  * Select `Custom Search` and provide the company name and name for the Application
  * Create a Datastore and select the Cloud Storage (GCS) --> Unstructured Documents. 
  * Select the bucket where your Knowledbase documents are stored. These could be user guides and technical docs. Leave all other settings to the default
  * Create the Application. Copy the Application ID from the Application list.
      
4.  **Configure Environment Variables:**
    *   Copy the example environment file to create your own local configuration:
        ```bash
        cp .env.example .env
        ```
    *   Open the newly created `.env` file in a text editor.
    *   Fill in the required values based on the comments within the file. This includes:
        *   `GOOGLE_GENAI_USE_VERTEXAI`: Choose `0` for ML Dev backend or `1` for Vertex AI.
        *   `GOOGLE_API_KEY`: Required if using the ML Dev backend.
        *   `GOOGLE_CLOUD_PROJECT`: Required if using the Vertex AI backend.
        *   `GOOGLE_CLOUD_LOCATION`: Required if using the Vertex AI backend.
        *   `GOOGLE_PLACES_API_KEY`: Your API key for the Google Places API. Ensure the "Places API" is enabled in your Google Cloud Project.
        *   `VERTEX_AI_SEARCH_LOCATION`: The location for your Vertex AI Search instance (e.g., `global`, `us-central1`).
        *   `VERTEX_AI_SEARCH_ENGINE_ID`: The ID of your Vertex AI Search application or datastore.
        *   `AGENT_COMPANY_NAME`: The name of the company the bot will represent (e.g., "ACME Corp").
        *   `AGENT_DOMAIN_NAME`: The domain name for constructing URLs (e.g., `acme-corp.com`).
        *   `GOOGLE_CLOUD_STORAGE_BUCKET` (Optional): A Google Cloud Storage bucket name, typically used for agent engine deployment tests.

5. **Create DocAI Processors:**
    * Run the script to create all the processors
  ```bash
    docai/create_docai_processor.sh
  ```
## Run Integration Test
Run integration test to confirm tools are connecting properly
```bash
poetry install --with dev
poetry run pytest

```

## Running the Application

*To run the application, execute the ADK web server using Poetry:*
```bash
poetry run adk web
```
This will start the ADK development UI, typically accessible at `http://localhost:8000`.

## Demo Script
**User:** `Hi`

**Expected Agent Response:**
``` 
I am a ACME Corp Point of Sale agent that can help you learn more about our POS solutions and choose the one right for you. I can guide you to purchasing one that is right for your business. 

To get started, could you please provide the name and location of your business?
```

---

**User:** `Not Just Coffee in Charlotte NC`

**Expected Agent Response:**
```
Okay, I found a few places. Let's see if any of these is your business.

Is this your business?

*   **Business Name**: Not Just Coffee
*   **Address**: 2230 Park Rd #102, Charlotte, NC 28203, USA
*   **Highlights**: Contemporary spot serving high-end coffee drinks, plus tea & light fare like toasts & yogurt.
*   **Image**: [View Image](https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=AXQCQNTG04QcYsV6q8JfNAMSU8rMfZMqHWGgUFdlTiH2I6gX6ewCSsy_6On3536ppRZ9gst9Srmp313GqeM5E_VROfNb6kBbEWLEGC9FI9N494QGt6t8JoKQJPv7ZWM6uf_KXyhU8ZunsBF2JC5ZvggmsIa16uZprHjw-takvQB315pn5PAQRFovZGD2lYJJryG2Vncc-IVGoFxyATlf7ijpWQNTuepRA2EwdB61y2RrUJmieKRqwnzpZPFVAkk11ZPpngarD6Uln8B9A7lokGsqCqvs5h9tqfA1W35rpwyFl67LxkUB6Kq8gJ56knOXywxCLq8-ThF6DC4jjogcgzR6qL0-xa7l3Yuy4xxZQaUJgI0KuBPpVcc1T9OHI39t-Ryjfheb2MJe6kEgcZ6wsWA7IdOA4Uzf33IgheWsMYtjHvZKq7PZoMgtHhP0FKKmoqgC9QvbQwIMOpnSvPJ1rEeMxC1at6uj_dDEyHOyYWT69lRW6mTRvnKTcYaZ-gSMC6CxwFy3NS60LcoDVPm7Cbq-hCd2SYHqbqTDu5hbZdRHgV6uVeFFJhSglhN66cvDFG2yiHz7hIN3Y2WBwugZjMlwkm6zHjsnZ3yzNN1eQHwLX6uHBGS6zah-lTp0WkdgppmqeH6pW98H&key=AIzaSyDUeMiCdcrp1GMUksbatZNKalKCVEffdcs)
*   **Map**: [View on Google Maps](https://www.google.com/maps/place/?q=place_id:ChIJmQuamJ-fVogRRVVKVkx3xjM)
*   **Place ID**: ChIJmQuamJ-fVogRRVVKVkx3xjM
*   **Review Rating**: 4.4

Yes or No?
```
**Expected Tool Use:**
*   transfer_to_agent
*   find_business_from_google_maps

---

**User:** `Yes`

**Expected Agent Response:**
```
Great! Now that I have your business information, the next step is to look at your current POS setup. Could you please upload a picture of your current Point of Sale system? This will help me recommend the best ACME Corp solution for Not Just Coffee.
```
**Expected Tool Use:**
*   transfer_to_agent

---

**User:** Click the Attach icon to upload the [image of the POS](./tests/data/input_image.jpeg) `Here you go`

**Expected Agent Response:**
```
Thanks for providing the image. It looks like you're currently using the Square Register.

Considering Not Just Coffee is a coffee shop, which falls under the quick-service restaurant category, and you are currently using a stationary system, I would recommend the following two ACME Corp POS terminals:

1.  **ACME Corp Station Solo:** This is a stationary system ideal for retail and quick-service restaurants. It features a large merchant screen, receipt printer, and an optional cash drawer. It has strong processing capabilities and supports various payment types, inventory management, order management, customer engagement, employee management, reporting, and online ordering integration.

2.  **ACME Corp Mini:** This is also a stationary, compact countertop system suitable for retail, quick-service restaurants, and services. It has a compact design with a touchscreen and built-in printer. It accepts various payment types and offers inventory management, order management, customer engagement, employee management, reporting, and online ordering integration, and appointment management which could be useful for your coffee shop.

Both of these options would be a great fit for your business based on your current setup and business type.

Would you like to finalize either the ACME Corp Station Solo or the ACME Corp Mini for your business?
```
**Expected Tool Use:**
*   identify_pos_model

---

**User:** `What are the steps to install the Solo`

**Expected Agent Response:**
```
Here are the installation steps for the ACME Corp Station Solo:

- The Station Solo includes the main unit.
- Flex and printer are sold separately.
- The charging cable accessory is sold separately.
- Step 1 & 2: Connect two cables to the back of the device.
- Step 3: Connect a cable to a device.
- Step 4: Connect a cable to a power adapter.
- Plug in last, to a grounded AC power outlet.

Here are some resources with more information:
*   <[relevant-document1.pdf](https://linkto-relevant-document1.pdf)>
*   <[relevant-document2.pdf](https://linkto-relevant-document2.pdf)>

Would you like to finalize either the ACME Corp Station Solo or the ACME Corp Mini for your business?
```
**Expected Tool Use:**
*   knowledgebase_search_agent

---

**User:** `I like the Solo`

**Expected Agent Response:**
```
Great, the ACME Corp Station Solo is an excellent choice for a business like yours!

Would you like to see how the ACME Corp Station Solo would look in your store based on the image you provided earlier?
```
**Expected Tool Use:**
*   (No tool use)

---

**User:** `Yes`

**Expected Agent Response:** 

Modified image is shown with new model user selected in the foreground but the same backgound.
```
Here is how the ACME Corp Station Solo would look in your store:

Would you like to finalize the order for the ACME Corp Station Solo?
```
**Expected Tool Use:**
*   image_editor

---

**User:** `Yes`

**Expected Agent Response:**
```
Let's verify your identity so we can get a price and contract started. Please submit upload your drivers licence:
```
**Expected Tool Use:**
*   update_opportunity_stage
*   transfer_to_agent

---

**User:** Click the Attach icon to upload the [Drivers License](./tests/data/DL-brenda-sample.jpeg `Here`

**Expected Agent Response:**
```
 Great. Now please submit upload a copy of your Bank Statement:
```

**Expected Tool Use:**
*   check_fraud_drivers_license
*   extract_info_from_drivers_license

**User:** Click the Attach icon to upload the [Drivers License](./tests/data/DL-brenda-sample.jpeg `Here`

---

**User:** Click the Attach icon to upload the [Bank Statement](./tests/data/Bank-Statement-brenda-sample.pdf `Here`

**Expected Agent Response:**
```

 - Type of first document: Drivers License
 - Type of second document: Bank Statement
 - Names are matching in both documents: Yes
 
Congratulations on successfully verifying your identity!

You can now view the contract and purchase the POS system at: https://acme-corp.com/buynow/not-just-coffee-hyphenated

For any questions, please contact ACME Corp Sales at (555) 123-4567. Our contact details are also available on our website.
```

**Expected Tool Use:**
*   extract_info_from_bank_statement
---


## Development

The project includes tools for development and testing.

*   **Install Development Dependencies:**
    To include development-specific packages (like `pytest` for testing), run:
    ```bash
    poetry install --with dev
    ```

*   **Running Tests:**
    After installing development dependencies, you can run the test suite using:
    ```bash
    poetry run pytest
    ```

## Deployment

*   **Install Deployment Dependencies:**
    To include dependencies required for deployment, run:
    ```bash
    poetry install --with deployment
    ```
    *(Further deployment steps would be specific to your target environment.)*
