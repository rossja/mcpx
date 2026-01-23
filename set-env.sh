#!/bin/bash

# Script to set Heroku config vars from a .env file
# Usage: ./set-env.sh <app-name> [env-file]
# Example: ./set-env.sh mcpx .env

set -e

APP_NAME="${1:-}"
ENV_FILE="${2:-.env}"

if [ -z "$APP_NAME" ]; then
    echo "Usage: $0 <app-name> [env-file]"
    echo "Example: $0 mcpx .env"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

echo "Setting Heroku config vars for app '$APP_NAME' from '$ENV_FILE'..."

# Build config vars string, skipping comments and empty lines
CONFIG_VARS=""
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    
    # Skip lines without '='
    [[ ! "$line" =~ = ]] && continue
    
    # Add to config vars (space-separated for heroku config:set)
    CONFIG_VARS="$CONFIG_VARS $line"
done < "$ENV_FILE"

if [ -z "$CONFIG_VARS" ]; then
    echo "No config vars found in $ENV_FILE"
    exit 0
fi

# Set all vars in one command (more efficient)
echo "Running: heroku config:set$CONFIG_VARS -a $APP_NAME"
heroku config:set $CONFIG_VARS -a "$APP_NAME"

echo "Done!"
