#!/bin/bash
# Import environment variables
set -a
source .env
set +a


# Create Idenity Document Proofing Processor
curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d @docai/us-id-proofing.json \
    https://"${PROCESSOR_LOCATION}"-documentai.googleapis.com/v1/projects/"${GOOGLE_CLOUD_PROJECT}"/locations/"${PROCESSOR_LOCATION}"/processors \
  | jq '.name' \
  | sed 's/\(.*\)/ID_PROOFING_PROCESSOR_FULLPATH=\1/' \
  >> .env


# Create DL Processor
curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d @docai/us-dl-request.json \
    https://"${PROCESSOR_LOCATION}"-documentai.googleapis.com/v1/projects/"${GOOGLE_CLOUD_PROJECT}"/locations/"${PROCESSOR_LOCATION}"/processors \
  | jq '.name' \
  | sed 's/\(.*\)/DL_PROCESSOR_FULLPATH=\1/' \
  >> .env


# Create Bank Statement Processor
curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d @docai/us-bank-statement.json \
    https://"${PROCESSOR_LOCATION}"-documentai.googleapis.com/v1/projects/"${GOOGLE_CLOUD_PROJECT}"/locations/"${PROCESSOR_LOCATION}"/processors \
  | jq '.name' \
  | sed 's/\(.*\)/BANK_STATEMENT_PROCESSOR_FULLPATH=\1/' \
  >> .env

docai/set-bank-processor-version.sh