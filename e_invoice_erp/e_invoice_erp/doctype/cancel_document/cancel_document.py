from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from e_invoice_erp.e_invoice_erp.doctype.api_credentials.api_credentials import fetch_api_token
import requests

class CancelDocument(Document):
#     def on_update(self):
#         uuid = self.uuid
#         frappe.msgprint(f"Submission UID: {uuid}")
    def before_save(self):
        if not self.api_credentials:
            frappe.throw("Please select API Credentials before saving.")
        
        # Fetch the API Credentials document
        api_credentials_doc = frappe.get_doc("API Credentials", self.api_credentials)
        print(f"Fetched API Credentials: {api_credentials_doc}")

        # Ensure client_id and client_secret are available
        if not api_credentials_doc.client_id or not api_credentials_doc.client_secret:
            frappe.throw("Client ID or Client Secret is missing in the selected API Credentials.")
        
        # Generate the API token by calling the fetch_api_token method
        token = fetch_api_token(api_credentials_doc)
        if token:
            # Set the fetched token in the api_access_token field
            self.api_access_token = token  # Ensure this matches the actual fieldname
            # frappe.msgprint(f"API Token fetched and saved successfully.")
        else:
            frappe.throw("Failed to fetch the API token.")


    def on_submit(self):
        uuid = self.uuid
        # frappe.msgprint(f"Submission UID before save: {uuid}")
        response_data = self.cancel_document(self.api_access_token)
        # frappe.msgprint(f"Response Data: {response_data}")

        if response_data:
            try:
                # self.status = response_data.get("status")
                # self.save()
                frappe.msgprint("Document cancelled successfully.",response_data)
            except Exception as e:
                frappe.log_error(message=str(e), title="E-Invoice Response Error")
                frappe.msgprint(f"Error saving document: {str(e)}")
        else:
            frappe.throw("No data returned from e-invoice service. Please check logs list for details.")

    def cancel_document(self, api_access_token):
        try:
            

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "ERPNextPythonClient/1.0",
                "Authorization": f"Bearer {api_access_token}",
                "Accept": "application/json",
                "Accept-Language": "en",
            }

            body = {
                "status": "cancelled",
                "reason": self.reason  # Assuming self.reason is set correctly
            }

            cancel_document_url = f"https://preprod-api.myinvois.hasil.gov.my/api/v1.0/documents/state/{self.uuid}/state"

            response = requests.put(cancel_document_url, headers=headers, json=body)

            if response.status_code == 200:
                response_data = response.json()
                return response_data
            else:
                raise Exception(
                    f"Failed to cancel document with status code {response.status_code}: Please cheack document validation"
                )

        except Exception as e:
            frappe.log_error(message=str(e), title="E-Invoice API Error")
            frappe.msgprint(f"Failed to cancel document. Error: {str(e)}")
