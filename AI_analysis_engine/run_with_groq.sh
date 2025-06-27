#!/bin/bash
# Run workflow with Groq API

# Check if Groq API key is provided
if [ -z "$1" ]; then
  echo "Error: Groq API key not provided"
  echo "Usage: $0 <GROQ_API_KEY>"
  exit 1
fi

# Set Groq API key
export GROQ_API_KEY="$1"

# Run workflow
./workflow.sh