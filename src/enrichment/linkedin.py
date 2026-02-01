"""LinkedIn company and employee enrichment using Apify."""

import asyncio
import json
import re
from typing import Optional
from urllib.parse import urlparse

import requests
from apify_client import ApifyClient
from bs4 import BeautifulSoup
from loguru import logger

from ..config import get_settings
from ..constants import APIFY_ACTORS, TARGET_TITLES
from ..models import Company, DecisionMaker


class LinkedInFinder:
    """Find company and employee data on LinkedIn."""

    def __init__(self, api_token: Optional[str] = None):
        settings = get_settings()
        self.client = ApifyClient(api_token or settings.apify_api_token)

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from a URL."""
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc
        except Exception:
            return None

    def extract_linkedin_from_website(self, website_url: str) -> Optional[str]:
        """
        Try to find LinkedIn URL directly from the company's website HTML.
        Useful for checking footers and contact pages.
        """
        try:
            # Ensure URL has protocol
            if not website_url.startswith('http'):
                website_url = 'https://' + website_url

            logger.info(f"Scraping {website_url} for LinkedIn links...")
            
            # Set headers to look like a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(website_url, headers=headers, timeout=60)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links containing linkedin.com
            links = soup.find_all('a', href=re.compile(r'linkedin\.com/(?:company|in)/', re.I))
            
            for link in links:
                href = link.get('href', '')
                # Filter out share links
                if 'share' not in href and 'sharing' not in href:
                    logger.info(f"Found LinkedIn link on website: {href}")
                    return href
                    
            return None
            
        except Exception as e:
            logger.debug(f"Failed to scrape website for LinkedIn: {e}")
            return None

    def find_company_url(self, company_name: str, website_url: Optional[str] = None, primary_domain: Optional[str] = None) -> Optional[str]:
        """
        Find company's LinkedIn URL.
        Priority:
        1. Check website footer/HTML directly
        2. Google Search

        Args:
            company_name: Name of the company
            website_url: Company website URL (helps with matching)
            primary_domain: Real company domain (not myshopify.com)

        Returns:
            LinkedIn company URL or None
        """
        # 1. Try to find link on the website itself first (Most accurate)
        if website_url:
            direct_link = self.extract_linkedin_from_website(website_url)
            if direct_link:
                return direct_link

        # 2. Fallback to Google Search
        logger.info(f"Searching Google for LinkedIn URL for company: {company_name}")

        # Build search query - use primary_domain if available, filter out myshopify.com
        search_query = f"{company_name} site:linkedin.com/company"

        # Prefer primary_domain, then try to extract from website_url
        domain_for_search = primary_domain
        if not domain_for_search and website_url:
            extracted_domain = self._extract_domain(website_url)
            # Only use domain if it's not myshopify.com
            if extracted_domain and "myshopify.com" not in extracted_domain:
                domain_for_search = extracted_domain

        if domain_for_search:
            search_query = f"{company_name} {domain_for_search} site:linkedin.com/company"

        logger.debug(f"Searching Google for LinkedIn URL: {search_query}")

        try:
            run_input = {
                "queries": search_query,
                "maxPagesPerQuery": 1,
                "resultsPerPage": 5,
            }

            run = self.client.actor(APIFY_ACTORS["google_search"]).call(
                run_input=run_input
            )

            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items

            # Find LinkedIn company URL in results
            # Handle different response formats from Google Search scraper
            for item in dataset_items:
                # Check organic results if present
                organic_results = item.get("organicResults", [])
                for result in organic_results:
                    url = result.get("link") or result.get("url", "")
                    linkedin_url = self._extract_linkedin_url(url)
                    if linkedin_url:
                        return linkedin_url

                # Also check direct url/link fields
                for field in ["url", "link", "displayLink"]:
                    url = item.get(field, "")
                    linkedin_url = self._extract_linkedin_url(url)
                    if linkedin_url:
                        return linkedin_url

            logger.warning(f"No LinkedIn company URL found for: {company_name}")
            return None

        except Exception as e:
            logger.error(f"Error searching for LinkedIn URL: {e}")
            return None

    def _extract_linkedin_url(self, url: str) -> Optional[str]:
        """Extract and clean LinkedIn company URL from a string."""
        if not url or "linkedin.com/company/" not in url:
            return None

        match = re.search(r"(https?://[a-z]+\.linkedin\.com/company/[^/\?\s]+)", url)
        if match:
            linkedin_url = match.group(1)
            logger.info(f"Found LinkedIn URL: {linkedin_url}")
            return linkedin_url
        return None

    def _normalize_name(self, name: str) -> str:
        """Normalize company name for comparison."""
        import re
        # Remove common suffixes, special chars, convert to lowercase
        name = name.lower()
        name = re.sub(r'[^a-z0-9\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        # Remove common business suffixes
        for suffix in ['inc', 'llc', 'ltd', 'corp', 'company', 'co', 'myshopify', 'com']:
            name = re.sub(rf'\b{suffix}\b', '', name)
        return name.strip()

    def _names_match(self, name1: str, name2: str, threshold: float = 0.4) -> bool:
        """Check if two company names are similar enough."""
        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)

        # Check if one contains the other
        if n1 in n2 or n2 in n1:
            return True

        # Check word overlap
        words1 = set(n1.split())
        words2 = set(n2.split())
        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        min_words = min(len(words1), len(words2))
        similarity = overlap / min_words if min_words > 0 else 0

        return similarity >= threshold

    def find_company(self, company_name: str, website: Optional[str] = None, primary_domain: Optional[str] = None) -> Optional[dict]:
        """
        Find a company on LinkedIn.

        Args:
            company_name: Name of the company
            website: Company website URL (helps with matching)
            primary_domain: Real company domain (not myshopify.com)

        Returns:
            Dictionary with LinkedIn company data or None
        """
        logger.info(f"Searching LinkedIn for company: {company_name}")

        # Step 1: Find LinkedIn URL (Website scraping + Google Search)
        linkedin_url = self.find_company_url(company_name, website, primary_domain)
        if not linkedin_url:
            return None

        # Step 2: Scrape company data from LinkedIn URL
        try:
            run_input = {
                "url": [linkedin_url],
            }

            run = self.client.actor(APIFY_ACTORS["linkedin_company"]).call(
                run_input=run_input
            )

            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items

            if not dataset_items:
                logger.warning(f"No data returned for LinkedIn URL: {linkedin_url}")
                return None

            result = dataset_items[0]
            linkedin_company_name = result.get("name", "")

            # Validate: Check if LinkedIn company name matches our search
            if not self._names_match(company_name, linkedin_company_name):
                logger.warning(
                    f"LinkedIn company name mismatch: searched '{company_name}', "
                    f"found '{linkedin_company_name}' - skipping"
                )
                return None

            # Ensure we have the LinkedIn URL in the result
            if not result.get("linkedInUrl"):
                result["linkedInUrl"] = linkedin_url

            logger.info(f"Found LinkedIn company: {linkedin_company_name}")
            return result

        except Exception as e:
            logger.error(f"Error scraping LinkedIn company: {e}")
            return None

    def enrich_company(self, company: Company) -> Company:
        """
        Enrich a company object with LinkedIn data.

        Args:
            company: Company object to enrich

        Returns:
            Enriched Company object
        """
        linkedin_data = self.find_company(company.name, company.website, company.primary_domain)

        if linkedin_data:
            company.linkedin_url = linkedin_data.get("linkedInUrl")

            # Employee count - try multiple field names
            employee_count = (
                linkedin_data.get("numberOfEmployees") or
                linkedin_data.get("employeeCount") or
                linkedin_data.get("employee_count")
            )
            if employee_count:
                company.employee_count = int(employee_count) if isinstance(employee_count, (int, str)) else None
                logger.info(f"Found employee count: {company.employee_count}")

            # Industry
            company.industry = linkedin_data.get("Industry") or linkedin_data.get("industry")

            # Description
            company.description = linkedin_data.get("description") or company.description

            # Founded year - try multiple field names
            founded = linkedin_data.get("Founded") or linkedin_data.get("foundedYear")
            if founded:
                try:
                    company.founded_year = int(str(founded)[:4])
                except (ValueError, TypeError):
                    pass

            # Extract country from mainAddress or headquarters
            if not company.country:
                # Try mainAddress first (structured data)
                main_address = linkedin_data.get("mainAddress", {})
                if isinstance(main_address, dict):
                    company.country = main_address.get("addressCountry")

                # Try Headquarters string (e.g., "..., US")
                if not company.country:
                    hq_string = linkedin_data.get("Headquarters", "")
                    if hq_string and ", " in hq_string:
                        # Extract last part which is usually the country code
                        parts = hq_string.split(", ")
                        potential_country = parts[-1].strip()
                        if len(potential_country) == 2:
                            company.country = potential_country.upper()

                if company.country:
                    logger.info(f"Found country: {company.country}")

            # Extract real company website/domain from LinkedIn
            linkedin_website = linkedin_data.get("website") or linkedin_data.get("companyUrl")
            if linkedin_website:
                # Clean and extract domain
                domain = self._extract_domain(linkedin_website)
                # Filter out invalid domains (social media, link aggregators, etc.)
                invalid_domains = [
                    "myshopify.com", "linkedin.com", "linktr.ee", "linktree.com",
                    "facebook.com", "instagram.com", "twitter.com", "x.com",
                    "youtube.com", "tiktok.com", "bit.ly", "goo.gl"
                ]
                if domain and not any(invalid in domain for invalid in invalid_domains):
                    company.primary_domain = domain
                    logger.info(f"Found primary domain from LinkedIn: {domain}")

            # If no valid domain from LinkedIn, try to extract from original URL
            if not company.primary_domain and company.website:
                original_domain = self._extract_domain(company.website)
                if original_domain and "myshopify.com" not in original_domain:
                    company.primary_domain = original_domain
                    logger.info(f"Using original domain as primary: {original_domain}")

        return company

    def find_employees(
        self,
        company_linkedin_url: str,
        titles: Optional[list[str]] = None,
        max_results: int = 10,
    ) -> list[dict]:
        """
        Find employees at a company by title.

        Args:
            company_linkedin_url: LinkedIn URL of the company
            titles: List of job titles to search for
            max_results: Maximum number of employees to return

        Returns:
            List of employee data dictionaries
        """
        titles = titles or TARGET_TITLES

        logger.info(f"Searching for employees at: {company_linkedin_url}")
        logger.info(f"Target titles: {titles[:3]}...")

        try:
            run_input = {
                "companyUrls": [company_linkedin_url],
                "titleFilter": titles,
                "maxResults": max_results,
            }

            run = self.client.actor(APIFY_ACTORS["linkedin_employees"]).call(
                run_input=run_input
            )

            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items

            logger.info(f"Found {len(dataset_items)} employees")
            return dataset_items

        except Exception as e:
            logger.error(f"Error finding employees: {e}")
            return []

    def find_decision_makers(
        self,
        company: Company,
        max_results: int = 5,
    ) -> list[DecisionMaker]:
        """
        Find decision makers at a company.

        Args:
            company: Company object
            max_results: Maximum number of decision makers to return

        Returns:
            List of DecisionMaker objects
        """
        if not company.linkedin_url:
            logger.warning(f"No LinkedIn URL for company: {company.name}")
            return []

        employees = self.find_employees(
            company.linkedin_url,
            titles=TARGET_TITLES,
            max_results=max_results,
        )

        decision_makers = []
        for emp in employees:
            dm = DecisionMaker(
                name=emp.get("name", "Unknown"),
                title=emp.get("title"),
                linkedin_url=emp.get("linkedInUrl"),
                location=emp.get("location"),
            )
            decision_makers.append(dm)

        return decision_makers

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        url = url.lower()
        url = url.replace("https://", "").replace("http://", "")
        url = url.replace("www.", "")
        return url.split("/")[0]
