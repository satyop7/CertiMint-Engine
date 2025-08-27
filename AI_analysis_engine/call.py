import requests

OMNIDIMENSION_API_TOKEN = "your key" # Replace with your token
AGENT_ID = 2499 # Your CertiMint Voice Assistant's ID

def dispatch_omnidimension_call(to_number, customer_name=None, account_id=None):
        url = "https://backend.omnidim.io/api/v1/calls/dispatch"
        headers = {
            "Authorization": f"Bearer {OMNIDIMENSION_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "agent_id": AGENT_ID,
            "to_number": to_number,
            "call_context": {
                "customer_name": customer_name,
                "account_id": account_id
            }
        }
        # Remove None values from call_context if not needed
        payload["call_context"] = {k: v for k, v in payload["call_context"].items() if v is not None}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            print("Call dispatched successfully:", response.json())
            return response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            print(f"Response: {response.text}")
        except Exception as err:
            print(f"An error occurred: {err}")

    # Example usage (get to_number from your website form submission)
user_entered_phone = "+919875518960" # This would come from your frontend
dispatch_omnidimension_call(user_entered_phone, customer_name="Jane Doe")