"""Shopify store discovery using Apify."""

from typing import Optional

from apify_client import ApifyClient
from loguru import logger

from ..config import get_settings
from ..constants import APIFY_ACTORS, TARGET_COUNTRIES
from ..models import ShopifyStoreInfo


class ShopifyFinder:
    """Find Shopify stores using Apify scrapers."""

    def __init__(self, api_token: Optional[str] = None):
        settings = get_settings()
        self.client = ApifyClient(api_token or settings.apify_api_token)

    def search_by_keywords(
        self,
        keywords: list[str],
        countries: Optional[list[str]] = None,
        max_results: int = 100,
    ) -> list[ShopifyStoreInfo]:
        """
        Search for Shopify stores by keywords using Google Search Scraper.
        """
        countries = countries or TARGET_COUNTRIES
        
        # Create a Google search query specifically for Shopify stores
        # Example: "sunglasses site:myshopify.com"
        queries = [f"{kw} site:myshopify.com" for kw in keywords[:5]] # Keep it reasonable
        
        logger.info(f"Searching for Shopify stores using Google Search. Keywords: {keywords}")
        
        results = []
        try:
            run_input = {
                "queries": "\n".join(queries),
                "maxPagesPerQuery": 1,
                "resultsPerPage": 20,
                "mobileResults": False,
            }

            run = self.client.actor(APIFY_ACTORS["google_search"]).call(
                run_input=run_input
            )

            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items

            seen_urls = set()
            for item in dataset_items:
                # Google Search Scraper returns organic results in 'organicResults'
                for result in item.get("organicResults", []):
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        # Basic check to see if it's a shopify store or at least looks like one
                        if "myshopify.com" in url or "products" in url:
                            store = ShopifyStoreInfo(
                                url=url,
                                name=result.get("title"),
                                description=result.get("description"),
                                is_shopify=True,
                            )
                            results.append(store)
                            seen_urls.add(url)
                    
                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break

            logger.info(f"Found {len(results)} potential Shopify stores through Google")

        except Exception as e:
            logger.error(f"Error searching through Google: {e}")
            raise

        return results

    def get_store_info(self, store_url: str) -> Optional[ShopifyStoreInfo]:
        """
        Get detailed information about a specific Shopify store.

        Args:
            store_url: URL of the Shopify store

        Returns:
            ShopifyStoreInfo object or None if not found
        """
        logger.info(f"Getting store info for: {store_url}")

        try:
            run_input = {
                "startUrls": [{"url": store_url}],
            }

            run = self.client.actor(APIFY_ACTORS["shopify_store_info"]).call(
                run_input=run_input
            )

            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items

            if dataset_items:
                item = dataset_items[0]
                return ShopifyStoreInfo(
                    url=item.get("url", store_url),
                    name=item.get("name"),
                    description=item.get("description"),
                    email=item.get("email"),
                    country=item.get("country"),
                    currency=item.get("currency"),
                    product_count=item.get("productCount"),
                    is_shopify=True,
                )

        except Exception as e:
            logger.error(f"Error getting store info for {store_url}: {e}")

        return None

    def search_epharmacy(
        self,
        languages: Optional[list[str]] = None,
        max_results: int = 50,
    ) -> list[ShopifyStoreInfo]:
        """Search for e-pharmacy Shopify stores."""
        from ..constants import KEYWORDS_EPHARMACY

        languages = languages or ["en", "de", "fr", "es", "nl", "it", "fi"]

        all_keywords = []
        for lang in languages:
            if lang in KEYWORDS_EPHARMACY:
                all_keywords.extend(KEYWORDS_EPHARMACY[lang])

        return self.search_by_keywords(all_keywords, max_results=max_results)

    def search_eyewear(self, max_results: int = 50) -> list[ShopifyStoreInfo]:
        """Search for eyewear/sunglasses Shopify stores."""
        from ..constants import KEYWORDS_EYEWEAR

        return self.search_by_keywords(KEYWORDS_EYEWEAR, max_results=max_results)
