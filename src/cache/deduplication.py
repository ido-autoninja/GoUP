"""URL/Domain deduplication cache."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from loguru import logger


class DeduplicationCache:
    """
    Cache for tracking processed domains to prevent duplicate processing.

    Stores processed domains with their lead_id and timestamp in a JSON file.
    """

    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize the deduplication cache.

        Args:
            cache_file: Path to the cache file. Defaults to data/processed_domains.json
        """
        if cache_file is None:
            cache_file = Path("data/processed_domains.json")

        self.cache_file = cache_file
        self._cache: dict = {}
        self._load_cache()

    def _load_cache(self):
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self._cache = json.load(f)
                logger.debug(f"Loaded {len(self._cache)} domains from cache")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache: {e}")
                self._cache = {}
        else:
            self._cache = {}

    def _save_cache(self):
        """Save cache to file."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Failed to save cache: {e}")

    def normalize_url(self, url: str) -> str:
        """
        Normalize a URL to extract the base domain.

        Removes:
            - Protocol (http/https)
            - www prefix
            - Query parameters
            - Trailing slashes
            - Path components

        Args:
            url: URL to normalize

        Returns:
            Normalized domain string
        """
        url = url.lower().strip()

        # Remove protocol
        url = url.replace("https://", "").replace("http://", "")

        # Remove www
        url = url.replace("www.", "")

        # Get just the domain (remove path, query, etc.)
        try:
            # Handle URLs that might still have path components
            domain = url.split("/")[0]
            domain = domain.split("?")[0]
            domain = domain.split("#")[0]
        except Exception:
            domain = url

        return domain.strip()

    def is_processed(self, url: str) -> bool:
        """
        Check if a domain has already been processed.

        Args:
            url: URL to check

        Returns:
            True if already processed, False otherwise
        """
        domain = self.normalize_url(url)
        return domain in self._cache

    def get_lead_id(self, url: str) -> Optional[str]:
        """
        Get the lead_id for a previously processed domain.

        Args:
            url: URL to check

        Returns:
            lead_id if found, None otherwise
        """
        domain = self.normalize_url(url)
        entry = self._cache.get(domain)
        if entry:
            return entry.get("lead_id")
        return None

    def mark_processed(self, url: str, lead_id: str):
        """
        Mark a domain as processed.

        Args:
            url: URL that was processed
            lead_id: ID of the lead created for this domain
        """
        domain = self.normalize_url(url)
        self._cache[domain] = {
            "lead_id": lead_id,
            "processed_at": datetime.utcnow().isoformat(),
        }
        self._save_cache()
        logger.debug(f"Marked domain as processed: {domain}")

    def remove(self, url: str):
        """
        Remove a domain from the cache.

        Args:
            url: URL to remove
        """
        domain = self.normalize_url(url)
        if domain in self._cache:
            del self._cache[domain]
            self._save_cache()
            logger.debug(f"Removed domain from cache: {domain}")

    def clear(self):
        """Clear all entries from the cache."""
        self._cache = {}
        self._save_cache()
        logger.info("Cleared deduplication cache")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            "total_domains": len(self._cache),
            "cache_file": str(self.cache_file),
        }

    def list_domains(self) -> list[str]:
        """
        List all cached domains.

        Returns:
            List of domain strings
        """
        return list(self._cache.keys())
