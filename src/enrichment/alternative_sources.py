"""Alternative sources for decision maker and company info."""

import re
from typing import Optional
from urllib.parse import urljoin

import httpx
from loguru import logger

from ..models import DecisionMaker


class AlternativeSourceFinder:
    """
    Find decision makers and company info from alternative sources.

    When LinkedIn and Hunter.io don't find decision makers,
    this scrapes About/Team pages and schema.org markup.
    """

    TIMEOUT = 60.0

    # Pages likely to contain team/founder info
    TEAM_PAGE_PATHS = [
        "/pages/about",
        "/pages/about-us",
        "/pages/our-story",
        "/pages/team",
        "/pages/our-team",
        "/pages/meet-the-team",
        "/about",
        "/about-us",
        "/team",
        "/our-story",
    ]

    # Title keywords for decision makers
    TITLE_KEYWORDS = [
        "founder",
        "co-founder",
        "ceo",
        "chief executive",
        "owner",
        "president",
        "managing director",
        "director",
        "head of",
    ]

    def __init__(self):
        self.client = httpx.Client(
            timeout=self.TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

    def find_decision_makers_from_website(self, url: str) -> list[DecisionMaker]:
        """
        Scrape website for decision maker information.

        Checks About/Team pages and schema.org Person markup.

        Args:
            url: Website URL

        Returns:
            List of DecisionMaker objects found
        """
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        decision_makers = []

        # Try schema.org first (most structured)
        dm = self._find_from_schema(url)
        if dm:
            decision_makers.append(dm)

        # Try team/about pages
        for path in self.TEAM_PAGE_PATHS:
            page_url = urljoin(url, path)
            dms = self._scrape_team_page(page_url)
            decision_makers.extend(dms)

            # Stop if we found some
            if len(decision_makers) >= 3:
                break

        # Deduplicate by name
        seen_names = set()
        unique_dms = []
        for dm in decision_makers:
            name_lower = dm.name.lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_dms.append(dm)

        if unique_dms:
            logger.info(f"Found {len(unique_dms)} decision makers from website")

        return unique_dms[:5]  # Return max 5

    def _find_from_schema(self, url: str) -> Optional[DecisionMaker]:
        """Extract decision maker from schema.org Person markup."""
        try:
            response = self.client.get(url)
            if response.status_code != 200:
                return None

            html = response.text

            # Look for schema.org JSON-LD
            import json
            schema_matches = re.findall(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html,
                re.DOTALL | re.IGNORECASE
            )

            for schema_text in schema_matches:
                try:
                    schema_data = json.loads(schema_text)
                    dm = self._extract_person_from_schema(schema_data)
                    if dm:
                        return dm
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            logger.debug(f"Schema extraction failed: {e}")

        return None

    def _extract_person_from_schema(self, data: dict) -> Optional[DecisionMaker]:
        """Recursively extract Person from schema.org data."""
        if isinstance(data, dict):
            schema_type = data.get("@type", "")

            # Check if this is a Person
            if schema_type == "Person" or (isinstance(schema_type, list) and "Person" in schema_type):
                name = data.get("name")
                if name:
                    title = data.get("jobTitle") or data.get("title")

                    # Check if it's a decision maker title
                    if title and any(kw in title.lower() for kw in self.TITLE_KEYWORDS):
                        return DecisionMaker(
                            name=name,
                            title=title,
                            email=data.get("email"),
                        )
                    elif not title:
                        # Person without title might still be relevant (founder)
                        return DecisionMaker(name=name)

            # Recurse into nested structures
            for value in data.values():
                result = self._extract_person_from_schema(value)
                if result:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = self._extract_person_from_schema(item)
                if result:
                    return result

        return None

    def _scrape_team_page(self, url: str) -> list[DecisionMaker]:
        """Scrape a team/about page for decision maker info."""
        decision_makers = []

        try:
            response = self.client.get(url)
            if response.status_code != 200:
                return []

            html = response.text

            # Look for common patterns of team member sections
            # Pattern 1: Name with title in nearby text
            # Look for patterns like "John Doe, CEO" or "John Doe - Founder"
            patterns = [
                # Name, Title pattern
                r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,\-\|:]\s*((?:CEO|Founder|Co-Founder|Owner|President|Managing Director|Director)[^<\n]{0,30})',
                # Title: Name pattern
                r'(CEO|Founder|Co-Founder|Owner|President)\s*[:\-]\s*([A-Z][a-z]+ [A-Z][a-z]+)',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    # Determine which group is name and which is title
                    if re.match(r'^[A-Z][a-z]+ [A-Z]', match[0]):
                        name = match[0].strip()
                        title = match[1].strip()
                    else:
                        name = match[1].strip()
                        title = match[0].strip()

                    # Clean up the title
                    title = re.sub(r'<[^>]+>', '', title)  # Remove HTML
                    title = title.strip('.,;:-')

                    if name and len(name) > 3 and len(name) < 50:
                        dm = DecisionMaker(name=name, title=title)
                        decision_makers.append(dm)

            # Also look for h2/h3/h4 followed by title-like text
            name_title_pattern = r'<h[2-4][^>]*>([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)</h[2-4]>\s*(?:<[^>]+>)*\s*((?:CEO|Founder|Co-Founder|Owner|President|Managing Director|Head of[^<]{0,30}))'
            matches = re.findall(name_title_pattern, html, re.IGNORECASE)
            for name, title in matches:
                name = name.strip()
                title = re.sub(r'<[^>]+>', '', title).strip()
                if name and len(name) > 3 and len(name) < 50:
                    dm = DecisionMaker(name=name, title=title)
                    decision_makers.append(dm)

        except Exception as e:
            logger.debug(f"Team page scraping failed for {url}: {e}")

        return decision_makers

    def get_contact_email(self, url: str) -> Optional[str]:
        """
        Get any contact email from the website.

        Args:
            url: Website URL

        Returns:
            Email address or None
        """
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        contact_paths = ["/pages/contact", "/contact", "/contact-us", "/"]

        for path in contact_paths:
            try:
                page_url = urljoin(url, path)
                response = self.client.get(page_url)

                if response.status_code == 200:
                    # Find email addresses
                    emails = re.findall(
                        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                        response.text
                    )

                    # Filter out common non-contact emails
                    excluded = ['example', 'email', 'your', 'shopify', 'sentry', 'test', 'noreply']
                    for email in emails:
                        if not any(x in email.lower() for x in excluded):
                            logger.info(f"Found contact email: {email}")
                            return email

            except Exception:
                continue

        return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
