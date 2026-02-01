"""Shopify platform verification module."""

import json
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from loguru import logger

from ..models import Platform


# Currency to country mapping
CURRENCY_COUNTRY_MAP = {
    "USD": "US",
    "EUR": "DE",  # Default to Germany for EUR, can be overridden
    "GBP": "GB",
    "CAD": "CA",
    "AUD": "AU",
    "CHF": "CH",
    "SEK": "SE",
    "NOK": "NO",
    "DKK": "DK",
    "PLN": "PL",
    "CZK": "CZ",
    "HUF": "HU",
    "RON": "RO",
    "BGN": "BG",
    "HRK": "HR",
    "ISK": "IS",
    "JPY": "JP",
    "NZD": "NZ",
    "SGD": "SG",
    "HKD": "HK",
    "MXN": "MX",
    "BRL": "BR",
    "INR": "IN",
    "ZAR": "ZA",
}

# TLD to country mapping
TLD_COUNTRY_MAP = {
    ".com": None,  # Too generic
    ".co.uk": "GB",
    ".uk": "GB",
    ".de": "DE",
    ".fr": "FR",
    ".es": "ES",
    ".it": "IT",
    ".nl": "NL",
    ".be": "BE",
    ".at": "AT",
    ".ch": "CH",
    ".se": "SE",
    ".no": "NO",
    ".dk": "DK",
    ".fi": "FI",
    ".pt": "PT",
    ".ie": "IE",
    ".pl": "PL",
    ".cz": "CZ",
    ".hu": "HU",
    ".ca": "CA",
    ".au": "AU",
    ".nz": "NZ",
    ".jp": "JP",
    ".sg": "SG",
    ".hk": "HK",
    ".in": "IN",
    ".br": "BR",
    ".mx": "MX",
    ".za": "ZA",
}


class ShopifyVerifier:
    """Verify if a website is running on Shopify."""

    SHOPIFY_INDICATORS = [
        "cdn.shopify.com",
        "shopify.com/s/",
        "Shopify.theme",
        "shopify-section",
        'name="shopify-',
        "window.Shopify",
    ]

    TIMEOUT = 60.0

    def __init__(self):
        self.client = httpx.Client(
            timeout=self.TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

    def verify(self, url: str) -> dict:
        """
        Verify if a URL is a Shopify store.

        Returns dict with:
            - is_shopify: bool
            - platform: Platform enum
            - store_url: normalized URL
            - detection_method: how it was detected
            - error: error message if any
        """
        result = {
            "is_shopify": False,
            "platform": Platform.UNKNOWN,
            "store_url": url,
            "detection_method": None,
            "error": None,
        }

        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        result["store_url"] = url

        try:
            # Method 1: Check /products.json endpoint
            if self._check_products_json(url):
                result["is_shopify"] = True
                result["platform"] = Platform.SHOPIFY
                result["detection_method"] = "products.json"
                logger.info(f"✓ {url} - Shopify detected via products.json")
                return result

            # Method 2: Check page source for Shopify indicators
            method = self._check_page_source(url)
            if method:
                result["is_shopify"] = True
                result["platform"] = Platform.SHOPIFY
                result["detection_method"] = method
                logger.info(f"✓ {url} - Shopify detected via {method}")
                return result

            # Not Shopify
            result["platform"] = Platform.CUSTOM
            logger.info(f"✗ {url} - Not a Shopify store")

        except httpx.RequestError as e:
            result["error"] = str(e)
            logger.warning(f"✗ {url} - Request error: {e}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"✗ {url} - Unexpected error: {e}")

        return result

    def _check_products_json(self, url: str) -> bool:
        """Check if /products.json endpoint exists (Shopify-specific)."""
        try:
            products_url = urljoin(url, "/products.json")
            response = self.client.get(products_url)

            if response.status_code == 200:
                # Verify it's actually JSON with products
                try:
                    data = response.json()
                    return "products" in data
                except Exception:
                    return False
        except Exception:
            pass
        return False

    def _check_page_source(self, url: str) -> Optional[str]:
        """Check page source for Shopify indicators."""
        try:
            response = self.client.get(url)
            if response.status_code != 200:
                return None

            html = response.text.lower()

            for indicator in self.SHOPIFY_INDICATORS:
                if indicator.lower() in html:
                    return f"source:{indicator}"

            # Check for Shopify meta tags
            if 'content="shopify"' in html:
                return "meta:shopify"

        except Exception:
            pass
        return None

    def verify_batch(self, urls: list[str]) -> list[dict]:
        """Verify multiple URLs."""
        results = []
        for url in urls:
            result = self.verify(url)
            results.append(result)
        return results

    def detect_country_from_currency(self, url: str) -> Optional[str]:
        """
        Detect country from Shopify store currency configuration.

        Args:
            url: Store URL

        Returns:
            ISO country code or None
        """
        try:
            response = self.client.get(url)
            if response.status_code != 200:
                return None

            html = response.text

            # Look for Shopify.currency in JavaScript
            currency_match = re.search(r'Shopify\.currency\s*=\s*["\']([A-Z]{3})["\']', html)
            if currency_match:
                currency = currency_match.group(1)
                country = CURRENCY_COUNTRY_MAP.get(currency)
                if country:
                    logger.debug(f"Detected country from currency {currency}: {country}")
                    return country

            # Look for currency in meta tags or JSON
            currency_meta = re.search(r'currency["\']?\s*[:=]\s*["\']([A-Z]{3})["\']', html)
            if currency_meta:
                currency = currency_meta.group(1)
                country = CURRENCY_COUNTRY_MAP.get(currency)
                if country:
                    logger.debug(f"Detected country from currency meta {currency}: {country}")
                    return country

        except Exception as e:
            logger.debug(f"Currency detection failed: {e}")

        return None

    def detect_country_from_schema(self, url: str) -> Optional[str]:
        """
        Detect country from schema.org addressCountry markup.

        Args:
            url: Store URL

        Returns:
            ISO country code or None
        """
        try:
            response = self.client.get(url)
            if response.status_code != 200:
                return None

            html = response.text

            # Look for schema.org JSON-LD
            schema_matches = re.findall(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html,
                re.DOTALL | re.IGNORECASE
            )

            for schema_text in schema_matches:
                try:
                    schema_data = json.loads(schema_text)
                    country = self._extract_country_from_schema(schema_data)
                    if country:
                        logger.debug(f"Detected country from schema.org: {country}")
                        return country
                except json.JSONDecodeError:
                    continue

            # Look for addressCountry in HTML
            country_match = re.search(
                r'addressCountry["\']?\s*[:=]\s*["\']([A-Z]{2})["\']',
                html,
                re.IGNORECASE
            )
            if country_match:
                country = country_match.group(1).upper()
                logger.debug(f"Detected country from HTML: {country}")
                return country

        except Exception as e:
            logger.debug(f"Schema detection failed: {e}")

        return None

    def _extract_country_from_schema(self, data: dict) -> Optional[str]:
        """Recursively extract addressCountry from schema.org data."""
        if isinstance(data, dict):
            # Check for addressCountry field
            if "addressCountry" in data:
                country = data["addressCountry"]
                if isinstance(country, str) and len(country) == 2:
                    return country.upper()
                elif isinstance(country, dict) and "name" in country:
                    # Could be a full country object
                    return None

            # Check for address field
            if "address" in data:
                result = self._extract_country_from_schema(data["address"])
                if result:
                    return result

            # Recurse into other fields
            for value in data.values():
                result = self._extract_country_from_schema(value)
                if result:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = self._extract_country_from_schema(item)
                if result:
                    return result

        return None

    def detect_country_from_tld(self, url: str) -> Optional[str]:
        """
        Detect country from URL TLD.

        Args:
            url: Store URL

        Returns:
            ISO country code or None
        """
        try:
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check each TLD mapping
            for tld, country in TLD_COUNTRY_MAP.items():
                if domain.endswith(tld) and country:
                    logger.debug(f"Detected country from TLD {tld}: {country}")
                    return country

        except Exception as e:
            logger.debug(f"TLD detection failed: {e}")

        return None

    def detect_country(self, url: str) -> Optional[str]:
        """
        Detect country using multiple methods.

        Priority:
        1. Schema.org markup
        2. Currency configuration
        3. TLD

        Args:
            url: Store URL

        Returns:
            ISO country code or None
        """
        # Try schema.org first (most reliable)
        country = self.detect_country_from_schema(url)
        if country:
            return country

        # Try currency
        country = self.detect_country_from_currency(url)
        if country:
            return country

        # Try TLD as fallback
        country = self.detect_country_from_tld(url)
        if country:
            return country

        return None

    def extract_store_info(self, url: str) -> dict:
        """
        Extract additional info from a Shopify store.

        Returns dict with:
            - name: Store name
            - email: Contact email
            - phone: Contact phone
            - address: Physical address
            - description: Store description
            - social_links: Social media URLs
            - real_domain: Real website domain (if different from Shopify)
            - country: Detected country code
        """
        info = {
            "name": None,
            "email": None,
            "phone": None,
            "address": None,
            "description": None,
            "social_links": {},
            "real_domain": None,
            "country": None,
        }

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            # Get main page
            response = self.client.get(url)
            if response.status_code != 200:
                return info

            html = response.text

            # Extract store name from title or og:site_name
            name_match = re.search(r'<title>([^<]+)</title>', html, re.I)
            if name_match:
                info["name"] = name_match.group(1).split('|')[0].split('–')[0].strip()

            og_name = re.search(r'property="og:site_name"\s+content="([^"]+)"', html, re.I)
            if og_name:
                info["name"] = og_name.group(1)

            # Extract description
            desc_match = re.search(r'name="description"\s+content="([^"]+)"', html, re.I)
            if desc_match:
                info["description"] = desc_match.group(1)

            # Extract email from page
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
            if email_match:
                email = email_match.group(0)
                # Filter out common non-contact emails
                if not any(x in email.lower() for x in ['example', 'email', 'your', 'shopify', 'sentry']):
                    info["email"] = email

            # Extract phone
            phone_match = re.search(r'tel:([+\d\s\-().]+)', html)
            if phone_match:
                info["phone"] = phone_match.group(1).strip()

            # Extract social links
            social_patterns = {
                "facebook": r'href="(https?://(?:www\.)?facebook\.com/[^"]+)"',
                "instagram": r'href="(https?://(?:www\.)?instagram\.com/[^"]+)"',
                "twitter": r'href="(https?://(?:www\.)?(?:twitter|x)\.com/[^"]+)"',
                "linkedin": r'href="(https?://(?:www\.)?linkedin\.com/(?:company|in)/[^"]+)"',
            }
            for platform, pattern in social_patterns.items():
                match = re.search(pattern, html, re.I)
                if match:
                    info["social_links"][platform] = match.group(1)

            # Try to find real domain (non-Shopify)
            # Look for canonical URL or links to main website
            canonical = re.search(r'rel="canonical"\s+href="(https?://[^"]+)"', html, re.I)
            if canonical:
                domain = canonical.group(1)
                if "myshopify.com" not in domain:
                    info["real_domain"] = re.sub(r'https?://(www\.)?', '', domain).split('/')[0]

            # Try /pages/contact for more info
            try:
                contact_response = self.client.get(urljoin(url, "/pages/contact"))
                if contact_response.status_code == 200:
                    contact_html = contact_response.text

                    # Look for email in contact page
                    if not info["email"]:
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', contact_html)
                        if email_match:
                            email = email_match.group(0)
                            if not any(x in email.lower() for x in ['example', 'email', 'your', 'shopify']):
                                info["email"] = email

                    # Look for address
                    address_match = re.search(
                        r'<address[^>]*>([^<]+(?:<[^>]+>[^<]+)*)</address>',
                        contact_html, re.I | re.S
                    )
                    if address_match:
                        info["address"] = re.sub(r'<[^>]+>', ' ', address_match.group(1)).strip()

            except Exception:
                pass

            # Detect country
            info["country"] = self.detect_country(url)

            logger.info(f"Extracted store info: name={info['name']}, email={info['email']}, country={info['country']}")

        except Exception as e:
            logger.debug(f"Error extracting store info: {e}")

        return info

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
