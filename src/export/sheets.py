"""Google Sheets export with OAuth authentication."""

import json
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from loguru import logger

from ..config import get_settings
from ..models import Lead


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsExporter:
    """Export leads to Google Sheets using OAuth."""

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        sheet_id: Optional[str] = None,
    ):
        settings = get_settings()
        self.credentials_file = credentials_file or settings.google_credentials_file
        self.token_file = token_file or settings.google_token_file
        self.sheet_id = sheet_id or settings.google_sheet_id
        self.service = None

    def authenticate(self) -> bool:
        """
        Authenticate with Google using OAuth.

        Returns:
            True if authentication successful
        """
        creds = None

        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing Google OAuth token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Credentials file not found: {self.credentials_file}")
                    logger.info("Please download OAuth credentials from Google Cloud Console")
                    return False

                logger.info("Starting OAuth flow - browser will open for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for future use
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
            logger.info(f"Token saved to {self.token_file}")

        self.service = build("sheets", "v4", credentials=creds)
        logger.info("Google Sheets authentication successful")
        return True

    def create_spreadsheet(self, title: str = "GoHub Leads") -> str:
        """
        Create a new spreadsheet with the required sheets.

        Returns:
            Spreadsheet ID
        """
        if not self.service:
            self.authenticate()

        spreadsheet = {
            "properties": {"title": title},
            "sheets": [
                {"properties": {"title": "Companies"}},
                {"properties": {"title": "Contacts"}},
                {"properties": {"title": "Outreach"}},
                {"properties": {"title": "Status"}},
            ],
        }

        result = self.service.spreadsheets().create(body=spreadsheet).execute()
        sheet_id = result["spreadsheetId"]

        logger.info(f"Created spreadsheet: {title}")
        logger.info(f"Sheet ID: {sheet_id}")
        logger.info(f"URL: https://docs.google.com/spreadsheets/d/{sheet_id}")

        self.sheet_id = sheet_id
        return sheet_id

    def setup_headers(self):
        """Set up headers for all sheets."""
        if not self.service or not self.sheet_id:
            raise ValueError("Must authenticate and have sheet_id first")

        headers = {
            "Companies": [
                "Lead ID", "Company Name", "Website", "Shopify URL", "Platform",
                "Industry", "Segment", "Country", "Employee Count", "LinkedIn URL",
                "Description", "Score", "Qualified"
            ],
            "Contacts": [
                "Lead ID", "Company Name", "Contact Name", "Title", "LinkedIn URL",
                "Email", "Email Verified", "Phone", "Location"
            ],
            "Outreach": [
                "Lead ID", "Company Name", "Contact Name", "Research Summary",
                "LinkedIn Request", "LinkedIn Follow-up", "Email Subject", "Email Body"
            ],
            "Status": [
                "Lead ID", "Company Name", "Status", "Notes", "Created Date",
                "Last Updated"
            ],
        }

        for sheet_name, header_row in headers.items():
            self._update_range(f"{sheet_name}!A1", [header_row])

        logger.info("Headers set up for all sheets")

    def export_leads(self, leads: list[Lead]):
        """
        Export leads to Google Sheets.

        Args:
            leads: List of Lead objects to export
        """
        if not self.service:
            self.authenticate()

        if not self.sheet_id:
            self.sheet_id = self.create_spreadsheet()
            self.setup_headers()

        # Prepare data for each sheet
        companies_data = []
        contacts_data = []
        outreach_data = []
        status_data = []

        for lead in leads:
            c = lead.company
            dm = lead.decision_maker
            o = lead.outreach
            q = lead.qualification

            # Companies sheet
            companies_data.append([
                lead.lead_id,
                c.name,
                c.website,
                c.shopify_url or "",
                c.platform.value if c.platform else "",
                c.industry or "",
                c.segment.value if c.segment else "",
                c.country or "",
                c.employee_count or "",
                c.linkedin_url or "",
                c.description or "",
                q.score,
                "Yes" if q.qualified else "No",
            ])

            # Contacts sheet
            if dm:
                contacts_data.append([
                    lead.lead_id,
                    c.name,
                    dm.name,
                    dm.title or "",
                    dm.linkedin_url or "",
                    dm.email or "",
                    "Yes" if dm.email_verified else "No",
                    dm.phone or "",
                    dm.location or "",
                ])

            # Outreach sheet
            if o:
                outreach_data.append([
                    lead.lead_id,
                    c.name,
                    dm.name if dm else "",
                    o.research_summary or "",
                    o.linkedin_connection_request or "",
                    o.linkedin_followup or "",
                    o.email_subject or "",
                    o.email_body or "",
                ])

            # Status sheet
            status_data.append([
                lead.lead_id,
                c.name,
                lead.status.value,
                lead.notes or "",
                lead.created_at.isoformat() if lead.created_at else "",
                lead.updated_at.isoformat() if lead.updated_at else "",
            ])

        # Write to sheets (append after headers)
        if companies_data:
            self._append_data("Companies", companies_data)
        if contacts_data:
            self._append_data("Contacts", contacts_data)
        if outreach_data:
            self._append_data("Outreach", outreach_data)
        if status_data:
            self._append_data("Status", status_data)

        logger.info(f"Exported {len(leads)} leads to Google Sheets")
        logger.info(f"Sheet URL: https://docs.google.com/spreadsheets/d/{self.sheet_id}")

    def _update_range(self, range_name: str, values: list):
        """Update a range of cells."""
        body = {"values": values}
        self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        ).execute()

    def _append_data(self, sheet_name: str, values: list):
        """Append data to a sheet."""
        body = {"values": values}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range=f"{sheet_name}!A:A",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()
