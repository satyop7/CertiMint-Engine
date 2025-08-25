
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
import json  # Added missing import
from fastapi.middleware.cors import CORSMiddleware
import ngrok
import uvicorn

# Configure ngrok
ngrok.set_auth_token("2sHa3Dcs1starAG1B1If9ZejoO2_6dtmkjPN38SPaHYx9vJqv")  

app = FastAPI()

# Allow all CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define data payload structure
class PDFPayload(BaseModel):
    userId: str
    fileUrl: str
    filename: str        # Changed from File_name to match what Node.js sends
    assignmentId: str    # Changed from assignmentID
    userName: str        # Changed from username
    subject: str         # Changed from subject_name
    strict_ai_detection: bool = True  # Default to True if not provided
    use_top_features: bool = True     # Default to True if not provided


# Upload directory setup
UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process")
async def process_pdf(payload: PDFPayload):
    user_id = payload.userId
    file_url = payload.fileUrl
    filename = payload.filename  # Now this matches the model
    assignment_id = payload.assignmentId
    name = payload.userName
    subject_name = payload.subject
    strict_ai_detection = bool(payload.strict_ai_detection)
    use_top_features = bool(payload.use_top_features)

    # Fetch PDF from the provided URL
    response = requests.get(file_url)
    if response.status_code != 200:
        return {"error": "Failed to download the PDF"}

    # Save PDF
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{filename}")
    with open(file_path, "wb") as f:
        f.write(response.content)

    print(f"📥 Received file from user '{user_id}': saved as {file_path}")

    # Create JSON metadata
    metadata = {
        "username": name,
        "subject_name": subject_name,
        "File_name": f"{user_id}_{filename}",
        "assignmentID": assignment_id,
        "strict_ai_detection": strict_ai_detection,
        "use_top_features": use_top_features
    }

    # Save JSON file
    
    json_path = os.path.join(UPLOAD_DIR, "info.json")
    with open(json_path, "w") as jf:
        json.dump(metadata, jf, indent=4)

    return {
        "message": "PDF and metadata successfully stored",
        "stored_pdf": file_path,
        "metadata_json": json_path
    }

@app.get("/")
async def read_root():
    return {"message": "Server is running. Use /process endpoint to upload PDFs."}

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8000

    # Establish Ngrok tunnel
    listener = ngrok.forward(f"{host}:{port}", authtoken_from_env=False)
    public_url = listener.url()
    print(f"Ngrok tunnel established! Public URL: {public_url}")

    # Launch FastAPI server
    uvicorn.run(app, host=host, port=port, log_level="info")