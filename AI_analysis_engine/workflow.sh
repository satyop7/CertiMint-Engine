#!/bin/bash

echo "Starting Assignment Validation Workflow..."
echo "=========================================="

# Check if info.json exists
if [ ! -f "data/info.json" ]; then
    echo "Error: data/info.json not found"
    exit 1
fi

# Step 1: Pre-sandbox processing (OCR, web scraping, Groq)
echo "Step 1: Running pre-sandbox processing..."
python3 pre_sandbox.py

if [ $? -ne 0 ]; then
    echo "Error: Pre-sandbox processing failed"
    exit 1
fi

# Step 2: Run sandbox analysis directly (skip Docker for now)
echo "Step 2: Running sandbox analysis..."
python3 complete_workflow.py

if [ $? -ne 0 ]; then
    echo "Error: Sandbox analysis failed"
    exit 1
fi

# Step 3: Upload to MongoDB and cleanup
echo "Step 3: Uploading to MongoDB and cleanup..."
python3 upload_to_mongodb.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Analysis completed successfully!"
    echo "Result uploaded to MongoDB: certimint.assignments"
else
    echo "Warning: MongoDB upload failed, but analysis completed"
fi