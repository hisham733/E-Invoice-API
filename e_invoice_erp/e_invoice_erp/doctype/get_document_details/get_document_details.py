# -*- coding: utf-8 -*-
# Copyright (c) 2024, Alharazi_hisham and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import requests
import json
from datetime import datetime
from e_invoice_erp.e_invoice_erp.doctype.api_credentials.api_credentials import fetch_api_token

class GetDocumentDetails(Document):
	
    
    def before_save(self):
        if not self.api_credentials:
            frappe.throw("Please select API Credentials before saving.")
        
        # Fetch the API Credentials document
        api_credentials_doc = frappe.get_doc("API Credentials", self.api_credentials)

        # Ensure client_id and client_secret are available
        if not api_credentials_doc.client_id or not api_credentials_doc.client_secret:
            frappe.throw("Client ID or Client Secret is missing in the selected API Credentials.")
        
        # Generate the API token by calling the fetch_api_token method
        token = fetch_api_token(api_credentials_doc)
        if token:
            self.api_access_token = token  # Set the fetched token in the api_access_token field
        else:
            frappe.throw("Failed to fetch the API token.")

    def on_submit(self):
        uuid = self.uuid
        response_data = get_document_details(uuid, self.api_access_token)
        if response_data:
            try:
                # Save the raw response JSON in the `code` field
                self.code = json.dumps(response_data, indent=4)
                frappe.msgprint(f"Document details fetched and saved for UUID: {uuid}")
            except Exception as e:
                frappe.log_error(message=str(e), title="Error Saving Document Details")
                frappe.throw(f"Error while saving document details: {str(e)}")
        else:
            frappe.throw("No data returned from the e-invoice service. Please check logs for details.")


def get_document_details(uuid, api_access_token):
    """
    Fetch document details from the Get Document Details API
    :param uuid: The UUID of the document
    :param api_access_token: The access token for authentication
    :return: JSON response from the API
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_access_token}",
            "Accept": "application/json"
        }

        api_base_url = "https://preprod-api.myinvois.hasil.gov.my"
        get_document_details_url = f"{api_base_url}/api/v1.0/documents/{uuid}/details"

        # Make the GET request
        response = requests.get(get_document_details_url, headers=headers)

        if response.status_code == 200:
            # Parse and return the JSON response
            return response.json()
        else:
            frappe.log_error(f"Failed to fetch document details for UUID {uuid}. Status Code: {response.status_code}, Error: {response.text}")
            return None

    except Exception as e:
        frappe.log_error(f"Error fetching document details for UUID {uuid}: {str(e)}", "E-Invoice API Error")
        return None


def parse_datetime(datetime_str):
    """
    Helper function to parse and format datetime strings.
    """
    if datetime_str:
        try:
            dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            frappe.log_error(f"Error parsing datetime: {e}")
    return None
