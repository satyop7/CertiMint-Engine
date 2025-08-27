from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
import json
from fastapi.middleware.cors import CORSMiddleware
import ngrok
import uvicorn
import subprocess
import urllib3  # Add this for disabling warnings

# Disable SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure ngrok
ngrok.set_auth_token("2sHa3Dcs1starAG1B1If9ZejoO2_6dtmkjPN38SPaHYx9vJqv")  

app = FastAPI()

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
    filename: str
    assignmentId: str
    userName: str
    subject: str

# Upload directory setup
UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process")
async def process_pdf(payload: PDFPayload):
    user_id = payload.userId
    file_url = payload.fileUrl
    filename = payload.filename
    assignment_id = payload.assignmentId
    name = payload.userName
    subject_name = payload.subject

    # Fetch PDF
    try:
        response = requests.get(file_url)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return {"error": f"Failed to download the PDF: {str(e)}"}

    # Save PDF
    saved_pdf_name = f"{user_id}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, saved_pdf_name)
    with open(file_path, "wb") as f:
        f.write(response.content)

    print(f"📥 Received file from user '{user_id}': saved as {file_path}")

    # Save metadata JSON
    metadata = {
        "username": name,
        "subject_name": subject_name,
        "File_name": saved_pdf_name,
        "assignmentID": assignment_id,
    }
    json_path = os.path.join(UPLOAD_DIR, "info.json")
    with open(json_path, "w") as jf:
        json.dump(metadata, jf, indent=4)

    # ✅ Automatically trigger the bash script
    try:
        result_path = "result/result.json"
        result = subprocess.run(
            ["bash", "workflow.sh"],
            capture_output=True,
            text=True
        )
        print("✅ Bash script executed.")
        print("stdout:\n", result.stdout)
        print("stderr:\n", result.stderr)
        
        # Signal to core backend
        if os.path.exists(result_path):
            payload = {
                "userId": user_id,
                "assignmentId": assignment_id,
                "status": "Submitted",
                "feedback": "Your assignment has been reviewed & to check the result, please move to your dashboard.",
            }
            
            try:
                # Use verify=False to bypass SSL certificate verification
                send_signal = requests.post(
                    "https://certimint.onrender.com/receive-signal-from-ai-pipeline",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    verify=False  # Bypass SSL verification for self-signed cert
                )
                
                if send_signal.status_code == 200:
                    print("<= Signal sent to core backend successfully.")
                else:
                    print("Failed to send signal to core backend:", send_signal.text)
            except requests.exceptions.RequestException as e:
                print(f"Failed to send signal to backend: {e}")
        else:
            print("Result file not found:", result_path)
            return {
                "message": "PDF and metadata stored, but analysis result file not found.",
                "error": "Result file not generated."
            }
    except Exception as e:
        print("Error running analysis script:", str(e))
        return {
            "message": "PDF and metadata stored, but failed to run analysis script.",
            "error": str(e)
        }

    return {
        "message": "PDF, metadata stored and analysis triggered.",
        "stored_pdf": file_path,
        "metadata_json": json_path,
        "analysis_output": result.stdout.strip()
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