"""Main lead generation pipeline."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from .cache import DeduplicationCache
from .collectors import ShopifyFinder, ShopifyVerifier
from .config import get_settings
from .constants import SAMPLE_URLS
from .enrichment import AlternativeSourceFinder, EmailFinder, LinkedInFinder
from .export import GoogleSheetsExporter
from .models import Company, DecisionMaker, Lead, Platform, Segment
from .personalization import Copywriter
from .scoring import LeadScorer
from .validators import ProductValidator


class LeadGenerationPipeline:
    """End-to-end lead generation pipeline."""

    def __init__(self):
        self.settings = get_settings()
        self.verifier = ShopifyVerifier()
        self.finder = ShopifyFinder()
        self.product_validator = ProductValidator()
        self.dedup_cache = DeduplicationCache()
        self.linkedin = LinkedInFinder()
        self.email_finder = EmailFinder()
        self.alt_source_finder = AlternativeSourceFinder()
        self.scorer = LeadScorer()
        self.copywriter = Copywriter()
        self.exporter = GoogleSheetsExporter()

    def process_url(self, url: str, segment: Optional[Segment] = None, skip_validation: bool = False, force: bool = False) -> Optional[Lead]:
        """
        Process a single URL through the pipeline.

        Args:
            url: Website URL to process
            segment: Business segment (e-pharmacy, sunglasses, etc.)
            skip_validation: Skip product validation for eyewear stores
            force: Force reprocessing even if already in cache

        Returns:
            Lead object or None if processing failed
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {url}")
        logger.info(f"{'='*60}")

        # Check deduplication cache
        if not force and self.dedup_cache.is_processed(url):
            existing_lead_id = self.dedup_cache.get_lead_id(url)
            logger.info(f"⏭ Skipping already processed domain (lead_id: {existing_lead_id})")
            return None

        # Step 1: Verify Shopify
        logger.info("Step 1: Verifying Shopify platform...")
        verification = self.verifier.verify(url)

        platform = verification["platform"]
        if platform != Platform.SHOPIFY:
            logger.warning(f"Not a Shopify store, skipping: {url}")
            return None

        # Step 2: Validate eyewear products (for eyewear/sunglasses segment)
        if not skip_validation and segment in (Segment.EYEWEAR, Segment.SUNGLASSES):
            logger.info("Step 2: Validating eyewear products...")
            validation = self.product_validator.validate_eyewear_store(verification["store_url"])
            if not validation["is_eyewear_store"]:
                logger.warning(f"Not an eyewear store: {validation['rejection_reason']}")
                return None
            logger.info(f"✓ Eyewear store confirmed ({validation['eyewear_ratio']:.0%} eyewear products)")

        # Step 3: Extract store info from the website itself
        logger.info("Step 3: Extracting store info...")
        store_info = self.verifier.extract_store_info(verification["store_url"])

        # Step 4: Create initial lead
        lead_id = str(uuid.uuid4())[:8]

        # Extract domain - prioritize: store's real domain > canonical domain > original URL
        original_domain = self._extract_domain(url)
        primary_domain = None
        if store_info.get("real_domain"):
            primary_domain = store_info["real_domain"]
        elif "myshopify.com" not in original_domain:
            primary_domain = original_domain

        # Use extracted store name if available
        company_name = store_info.get("name") or self._extract_company_name(url)

        company = Company(
            name=company_name,
            website=url,
            shopify_url=verification["store_url"] if verification["is_shopify"] else None,
            primary_domain=primary_domain,
            platform=platform,
            segment=segment,
            description=store_info.get("description"),
            country=store_info.get("country"),  # Initial country from store detection
        )

        # Store LinkedIn URL if found on website
        if store_info.get("social_links", {}).get("linkedin"):
            company.linkedin_url = store_info["social_links"]["linkedin"]

        lead = Lead(lead_id=lead_id, company=company, source="manual")

        # Step 5: Hunter.io domain search FIRST (to get real domain for LinkedIn)
        hunter_data = None
        domain = company.primary_domain or self._extract_domain(url)
        if domain and "myshopify.com" not in domain:
            logger.info(f"Step 5: Searching Hunter.io for {domain}...")
            try:
                hunter_data = self.email_finder.domain_search(domain, limit=10)

                # Fill in missing company data from Hunter
                if hunter_data.get("company_name") and not company.name:
                    company.name = hunter_data["company_name"]
                if hunter_data.get("country") and not company.country:
                    company.country = hunter_data["country"]
                    logger.info(f"Got country from Hunter.io: {company.country}")
                if hunter_data.get("industry") and not company.industry:
                    company.industry = hunter_data["industry"]

                lead.company = company
            except Exception as e:
                logger.warning(f"Hunter.io search failed: {e}")

        # Step 6: Enrich with LinkedIn (now using real domain from Hunter.io)
        logger.info("Step 6: Enriching company data from LinkedIn...")
        try:
            company = self.linkedin.enrich_company(company)
            lead.company = company
        except Exception as e:
            logger.warning(f"LinkedIn enrichment failed: {e}")

        # Aggregate country from multiple sources (priority: LinkedIn > Hunter > Store > TLD)
        if not company.country:
            # Try TLD as final fallback
            tld_country = self.verifier.detect_country_from_tld(url)
            if tld_country:
                company.country = tld_country
                logger.info(f"Got country from TLD: {company.country}")

        if company.country:
            logger.info(f"Final country: {company.country}")

        # Step 7: Find decision makers (cascading fallback strategy)
        logger.info("Step 7: Finding decision makers...")

        # Strategy 1: LinkedIn employees search (if company URL exists)
        try:
            decision_makers = self.linkedin.find_decision_makers(company, max_results=3)
            if decision_makers:
                lead.decision_maker = decision_makers[0]  # Take top result
                logger.info(f"Found decision maker from LinkedIn: {lead.decision_maker.name}")
        except Exception as e:
            logger.warning(f"LinkedIn decision maker search failed: {e}")

        # Strategy 2: Hunter.io decision makers
        if not lead.decision_maker and hunter_data and hunter_data.get("decision_makers"):
            dm_data = hunter_data["decision_makers"][0]
            lead.decision_maker = DecisionMaker(
                name=dm_data["name"],
                title=dm_data.get("title"),
                email=dm_data.get("email"),
                email_verified=dm_data.get("confidence", 0) > 80,
            )
            logger.info(f"Found decision maker from Hunter.io: {lead.decision_maker.name}")

        # Strategy 3: Scrape About/Team pages
        if not lead.decision_maker:
            logger.info("Trying alternative sources (About/Team pages)...")
            try:
                alt_dms = self.alt_source_finder.find_decision_makers_from_website(
                    verification["store_url"]
                )
                if alt_dms:
                    lead.decision_maker = alt_dms[0]
                    logger.info(f"Found decision maker from website: {lead.decision_maker.name}")
            except Exception as e:
                logger.warning(f"Alternative source search failed: {e}")

        # Strategy 4: Store contact email as fallback (create minimal decision maker)
        if not lead.decision_maker and store_info.get("email"):
            logger.info("Using store contact email as fallback...")
            lead.decision_maker = DecisionMaker(
                name="Store Contact",
                email=store_info["email"],
            )

        # Step 8: Find and verify email
        if lead.decision_maker:
            # Check if we already have an email from Hunter.io
            if lead.decision_maker.email and lead.decision_maker.email_verified:
                logger.info(f"Using email from Hunter.io: {lead.decision_maker.email}")
            elif domain and "myshopify.com" not in domain:
                logger.info("Step 8: Finding and verifying email...")
                try:
                    lead.decision_maker = self.email_finder.enrich_decision_maker(
                        lead.decision_maker, domain
                    )
                except Exception as e:
                    logger.warning(f"Email finding failed: {e}")
        elif domain and "myshopify.com" not in domain:
            # No decision maker, but try to get any email from store info
            if store_info.get("email"):
                logger.info(f"Using email from store: {store_info['email']}")

        # Step 9: Score the lead
        logger.info("Step 9: Scoring lead...")
        lead = self.scorer.score(lead)

        # Step 10: Generate outreach copy for all Shopify stores
        if lead.company.platform == Platform.SHOPIFY:
            logger.info("Step 10: Generating personalized outreach copy...")
            try:
                self.copywriter.generate_outreach(lead)
                logger.info("✓ Outreach copy generated")
            except Exception as e:
                logger.warning(f"Copy generation failed: {e}")

        # Mark as processed in cache
        self.dedup_cache.mark_processed(url, lead.lead_id)

        logger.info(f"\nLead processed: {company.name}")
        logger.info(f"Score: {lead.qualification.score}")
        logger.info(f"Qualified: {'Yes' if lead.qualification.qualified else 'No'}")

        return lead

    def process_sample_urls(self) -> list[Lead]:
        """Process the sample URLs from configuration."""
        leads = []

        for sample in SAMPLE_URLS:
            url = sample["url"]
            segment_str = sample.get("segment", "")

            # Map segment string to enum
            segment = None
            if "pharmacy" in segment_str.lower():
                segment = Segment.EPHARMACY
            elif "sunglasses" in segment_str.lower():
                segment = Segment.SUNGLASSES
            elif "eyewear" in segment_str.lower():
                segment = Segment.EYEWEAR

            try:
                lead = self.process_url(url, segment=segment)
                if lead:
                    leads.append(lead)
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")

        return leads

    def process_urls(self, urls: list[str], force: bool = False) -> list[Lead]:
        """Process multiple URLs."""
        leads = []
        for url in urls:
            try:
                lead = self.process_url(url, force=force)
                if lead:
                    leads.append(lead)
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
        return leads

    def search_and_process(
        self,
        segment: str = "eyewear",
        max_results: int = 20,
        force: bool = False,
    ) -> list[Lead]:
        """
        Search for stores and process them.

        Args:
            segment: "eyewear" or "epharmacy"
            max_results: Maximum stores to find
            force: Force reprocessing of already-cached domains

        Returns:
            List of processed leads
        """
        logger.info(f"Searching for {segment} stores...")

        # Search for stores
        if segment == "epharmacy":
            stores = self.finder.search_epharmacy(max_results=max_results)
            seg = Segment.EPHARMACY
        else:
            stores = self.finder.search_eyewear(max_results=max_results)
            seg = Segment.EYEWEAR

        logger.info(f"Found {len(stores)} stores")

        # Process each store
        leads = []
        for store in stores:
            try:
                lead = self.process_url(store.url, segment=seg, force=force)
                if lead:
                    leads.append(lead)
            except Exception as e:
                logger.error(f"Failed to process {store.url}: {e}")

        return leads

    def export_to_sheets(self, leads: list[Lead]):
        """Export leads to Google Sheets."""
        logger.info("Exporting leads to Google Sheets...")
        self.exporter.export_leads(leads)

    def save_to_json(self, leads: list[Lead], filename: str = "leads.json"):
        """Save leads to JSON file."""
        output_path = self.settings.output_data_dir / filename

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = [lead.model_dump(mode="json") for lead in leads]

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {len(leads)} leads to {output_path}")

    def run_pilot(self) -> list[Lead]:
        """
        Run the pilot phase: process sample URLs and export.

        Returns:
            List of Shopify leads (with generated copy)
        """
        logger.info("\n" + "="*60)
        logger.info("STARTING PILOT RUN")
        logger.info("="*60 + "\n")

        # Process sample URLs
        leads = self.process_sample_urls()

        # Filter Shopify stores (they have outreach copy generated)
        shopify_leads = [l for l in leads if l.company.platform == Platform.SHOPIFY]

        logger.info(f"\n{'='*60}")
        logger.info("PILOT RESULTS")
        logger.info(f"{'='*60}")
        logger.info(f"Total processed: {len(leads)}")
        logger.info(f"Shopify stores: {len(shopify_leads)}")
        logger.info(f"Qualified leads (score >= 60): {len([l for l in leads if l.qualification.qualified])}")

        # Save results
        self.save_to_json(leads)

        # Print summary
        for lead in shopify_leads:
            logger.info(f"\n✓ {lead.company.name}")
            logger.info(f"  Score: {lead.qualification.score}")
            logger.info(f"  Has outreach copy: {'Yes' if lead.outreach else 'No'}")

        return shopify_leads

    def _extract_company_name(self, url: str) -> str:
        """Extract company name from URL."""
        domain = self._extract_domain(url)
        # Remove common TLDs and clean up
        name = domain.split(".")[0]
        return name.title()

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        url = url.lower()
        url = url.replace("https://", "").replace("http://", "")
        url = url.replace("www.", "")
        return url.split("/")[0]

    def close(self):
        """Clean up resources."""
        self.verifier.close()
        self.product_validator.close()
        self.email_finder.close()
        self.alt_source_finder.close()
