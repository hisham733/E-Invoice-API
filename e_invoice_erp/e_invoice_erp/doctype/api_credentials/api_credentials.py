from frappe.model.document import Document
import frappe
import requests
from datetime import datetime, timedelta
import pytz  # Ensure pytz is installed for timezone handling

# Global variables to store latest client_id and client_secret
latest_client_id =""
latest_client_secret="" 

class APICredentials(Document):
    pass  # This class can hold any document-related custom logic if needed.

@frappe.whitelist()
def fetch_api_token(doc=None, *args, **kwargs):
    """Fetch the API token using the Client ID and Client Secret from a document or fallback to global variables."""

    global latest_client_id, latest_client_secret

    if doc:
        client_id = doc.client_id
        client_secret = doc.client_secret
    else:
        # If doc is None, use the global variables
        client_id = latest_client_id
        client_secret = latest_client_secret

    # Check if client_id and client_secret are provided either from the doc or global variables
    if not client_id or not client_secret:
        frappe.throw("Client ID or Client Secret is missing. Please provide them either in the document or set globally.")

    api_base_url = "https://preprod-api.myinvois.hasil.gov.my"
    token_url = f"{api_base_url}/connect/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "ERPNextPythonClient/1.0",
        "Accept": "*/*",
    }

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "InvoicingAPI"
    }

    # Fetch the token from the API
    response = requests.post(token_url, headers=headers, data=payload)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")  # Token validity in seconds

        if not access_token:
            frappe.throw("No access token returned by the API. Please try again later.")

        # Update the global variables to store the successful client_id and client_secret
        latest_client_id = client_id
        latest_client_secret = client_secret
        print("latest_client_id",latest_client_id)

        # Calculate token expiration time in UTC
        expiration_time_utc = datetime.utcnow() + timedelta(seconds=expires_in)

        # Convert expiration time to Kuala Lumpur time (UTC+8)
        kl_zone = pytz.timezone("Asia/Kuala_Lumpur")
        expiration_time_kl = expiration_time_utc.astimezone(kl_zone)

        # Strip timezone information for MySQL compatibility
        expiration_time_kl_naive = expiration_time_kl.replace(tzinfo=None)

        # If a document is passed, save the token and expiration in the document
        if doc:
            doc.token = access_token
            doc.token_expiration = expiration_time_kl_naive
            # doc.save()

        frappe.msgprint(f"API Token fetched successfully. Token expires at {expiration_time_kl_naive} (Kuala Lumpur Time).")
        return access_token

    elif response.status_code == 400:
        frappe.throw("Failed to fetch API token. The Client ID or Client Secret may be incorrect. Please double-check your credentials and try again.")
    else:
        frappe.throw(f"Failed to fetch API token. Error {response.status_code}: {response.text}")