#!/usr/bin/env bash

json=$(cat <<EOF
{
  "JWT_token": "$1"
}
EOF
)

curl --insecure --header "Content-Type: application/json" \
  --request POST \
  --data "$json" \
  https://localhost/api/login
