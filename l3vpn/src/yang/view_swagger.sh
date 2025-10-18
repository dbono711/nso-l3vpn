#!/bin/sh

# This script starts a Docker container to view the local swagger.json file.

# Exit immediately if a command exits with a non-zero status.
set -e

CONTAINER_NAME="swagger-ui-l3vpn"
SWAGGER_FILE_PATH="${PWD}/swagger.json"

# Check if swagger.json exists
if [ ! -f "${SWAGGER_FILE_PATH}" ]; then
    echo "Error: swagger.json not found in the current directory."
    echo "Please generate it first."
    exit 1
fi

echo "Stopping and removing existing container if it exists..."
docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true

echo "Starting new Swagger UI container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    -p 8080:8080 \
    -v "${SWAGGER_FILE_PATH}":/usr/share/nginx/html/swagger.json \
    -e SWAGGER_JSON="swagger.json" \
    swaggerapi/swagger-ui

echo ""
echo "Swagger UI container '${CONTAINER_NAME}' started successfully."
echo "You can access the API documentation at: http://localhost:8080"

