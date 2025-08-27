#!/bin/bash

# Assignment Validation Workflow with Embedding Models
echo "🚀 Starting Assignment Validation Workflow"
echo "Using Embedding Models: all-MiniLM-L6-v2 + BAAI/bge-small-en"
echo "=================================================="

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "❌ Error: data/ directory not found"
    echo "Please create data/ directory and add your files:"
    echo "  - info.json (assignment metadata)"
    echo "  - assignment file (PDF/image)"
    exit 1
fi

# Check if info.json exists
if [ ! -f "data/info.json" ]; then
    echo "❌ Error: data/info.json not found"
    echo "Please create data/info.json with assignment metadata"
    exit 1
fi

# Run the complete workflow
echo "🔄 Running complete workflow..."
python3 complete_workflow.py

# Check if result was created
if [ -f "result/result.json" ]; then
    echo "✅ Workflow completed successfully!"
    echo "📄 Result saved to: result/result.json"
    
    # Display summary
    echo ""
    echo "📊 SUMMARY:"
    python3 -c "
import json
try:
    with open('result/result.json', 'r') as f:
        result = json.load(f)
    print(f\"Assignment ID: {result.get('assignment_id', 'N/A')}\")
    print(f\"Subject: {result.get('subject', 'N/A')}\")
    print(f\"Status: {result.get('status', 'N/A')}\")
    print(f\"Plagiarism: {result.get('plagiarism_check', {}).get('plagiarism_percentage', 0)}%\")
    print(f\"Relevance: {result.get('content_validation', {}).get('relevance_score', 0)}%\")
    print(f\"Model: Embedding-based (55MB total)\")
except Exception as e:
    print(f\"Error reading result: {e}\")
"
else
    echo "❌ Workflow failed - no result file generated"
    exit 1
fi

echo "=================================================="
echo "🎉 Workflow completed!"