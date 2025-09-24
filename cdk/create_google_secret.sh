#!/bin/bash

if [ -z "${GOOGLE_CLIENT_SECRET}" ]; then
  echo "GOOGLE_CLIENT_SECRET is not set"
  exit 1
fi


aws secretsmanager create-secret --name /diviz/google/oauth/client_secret --secret-string ${GOOGLE_CLIENT_SECRET}


