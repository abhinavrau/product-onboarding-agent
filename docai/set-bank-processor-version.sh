#!/bin/bash
# Import environment variables
set -a
source .env
set +a

curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "{ \"defaultProcessorVersion\": \"${BANK_STATEMENT_PROCESSOR_FULLPATH}/processorVersions/pretrained-bankstatement-v5.0-2023-12-06\" }" \
    https://"${PROCESSOR_LOCATION}"-documentai.googleapis.com/v1/"${BANK_STATEMENT_PROCESSOR_FULLPATH}":setDefaultProcessorVersion
