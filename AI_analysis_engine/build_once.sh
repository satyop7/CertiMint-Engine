#!/bin/bash

echo "Building Docker image for assignment validation..."
echo "This needs to be done only once."

# Build the Docker image
docker-compose build

echo "Docker image built successfully!"
echo "You can now run ./workflow.sh to perform analysis."