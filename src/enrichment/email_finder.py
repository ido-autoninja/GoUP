"""Email finding and verification using Hunter.io."""

from typing import Optional

import httpx
from loguru import logger

from ..config import get_settings
from ..models import DecisionMaker


class EmailFinder:
    """Find and verify email addresses using Hunter.io."""

    BASE_URL = "https://api.hunter.io/v2"

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.hunter_api_key
        self.client = httpx.Client(timeout=60.0)

    def find_email(
        self,
        domain: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Find email address for a person at a domain.

        Args:
            domain: Company domain (e.g., "example.com")
            first_name: Person's first name
            last_name: Person's last name
            full_name: Full name (will be split if first/last not provided)

        Returns:
            Dictionary with email data or None
        """
        # Parse full name if individual names not provided
        if full_name and not (first_name and last_name):
            parts = full_name.strip().split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            elif len(parts) == 1:
                first_name = parts[0]
                last_name = ""

        if not first_name:
            logger.warning("First name required for email finder")
            return None

        logger.info(f"Finding email for {first_name} {last_name} at {domain}")

        try:
            params = {
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name or "",
                "api_key": self.api_key,
            }

            response = self.client.get(f"{self.BASE_URL}/email-finder", params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("data", {}).get("email"):
                email_data = data["data"]
                logger.info(f"Found email: {email_data['email']} (score: {email_data.get('score', 'N/A')})")
                return {
                    "email": email_data["email"],
                    "score": email_data.get("score"),
                    "position": email_data.get("position"),
                    "sources": email_data.get("sources", []),
                }

            logger.warning(f"No email found for {first_name} {last_name} at {domain}")
            return None

        except httpx.HTTPStatusError as e:
            logger.error(f"Hunter.io API error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error finding email: {e}")
            return None

    def verify_email(self, email: str) -> dict:
        """
        Verify if an email address is valid and deliverable.

        Args:
            email: Email address to verify

        Returns:
            Dictionary with verification results
        """
        logger.info(f"Verifying email: {email}")

        try:
            params = {
                "email": email,
                "api_key": self.api_key,
            }

            response = self.client.get(f"{self.BASE_URL}/email-verifier", params=params)
            response.raise_for_status()

            data = response.json().get("data", {})

            result = {
                "email": email,
                "status": data.get("status"),  # valid, invalid, accept_all, unknown
                "score": data.get("score"),
                "deliverable": data.get("status") == "valid",
                "disposable": data.get("disposable", False),
                "webmail": data.get("webmail", False),
            }

            logger.info(f"Email {email} status: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return {
                "email": email,
                "status": "error",
                "deliverable": False,
                "error": str(e),
            }

    def domain_search(self, domain: str, limit: int = 10) -> dict:
        """
        Search for all email addresses and company info at a domain.

        Args:
            domain: Company domain
            limit: Maximum number of results

        Returns:
            Dictionary with company info and emails
        """
        logger.info(f"Searching Hunter.io for domain: {domain}")

        result = {
            "company_name": None,
            "country": None,
            "industry": None,
            "emails": [],
            "decision_makers": [],
        }

        try:
            params = {
                "domain": domain,
                "limit": limit,
                "api_key": self.api_key,
            }

            response = self.client.get(f"{self.BASE_URL}/domain-search", params=params)
            response.raise_for_status()

            data = response.json().get("data", {})

            # Extract company info
            result["company_name"] = data.get("organization")
            result["country"] = data.get("country")
            result["industry"] = data.get("industry")

            # Extract emails
            emails = data.get("emails", [])
            result["emails"] = emails

            # Find decision makers (executives with emails)
            executive_titles = ['ceo', 'founder', 'owner', 'director', 'president', 'chief', 'head']
            for email_data in emails:
                position = (email_data.get("position") or "").lower()
                if any(title in position for title in executive_titles):
                    result["decision_makers"].append({
                        "name": f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
                        "email": email_data.get("value"),
                        "title": email_data.get("position"),
                        "confidence": email_data.get("confidence"),
                    })

            logger.info(
                f"Hunter.io found: company={result['company_name']}, "
                f"country={result['country']}, {len(emails)} emails, "
                f"{len(result['decision_makers'])} decision makers"
            )

            return result

        except Exception as e:
            logger.error(f"Error searching domain: {e}")
            return result

    def enrich_decision_maker(
        self,
        decision_maker: DecisionMaker,
        domain: str,
    ) -> DecisionMaker:
        """
        Enrich a decision maker with email information.

        Args:
            decision_maker: DecisionMaker object
            domain: Company domain

        Returns:
            Enriched DecisionMaker object
        """
        if decision_maker.email and decision_maker.email_verified:
            return decision_maker

        # Find email
        email_data = self.find_email(domain, full_name=decision_maker.name)

        if email_data:
            decision_maker.email = email_data["email"]

            # Verify the email
            verification = self.verify_email(email_data["email"])
            decision_maker.email_verified = verification.get("deliverable", False)

        return decision_maker

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
