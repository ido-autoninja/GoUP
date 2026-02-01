"""Product validation for eyewear stores."""

import re
from typing import Optional
from urllib.parse import urljoin

import httpx
from loguru import logger

from ..constants import NEGATIVE_KEYWORDS_EYEWEAR


class ProductValidator:
    """Validate if a Shopify store sells eyewear products."""

    EYEWEAR_INDICATORS = [
        "glasses",
        "eyeglasses",
        "sunglasses",
        "eyewear",
        "optical",
        "frames",
        "lenses",
        "prescription",
        "reading glasses",
        "blue light",
        "spectacles",
        "rx",
        "vision",
        "aviator",
        "wayfarer",
        "polarized",
    ]

    TIMEOUT = 60.0
    MIN_EYEWEAR_RATIO = 0.30  # At least 30% of products should be eyewear

    def __init__(self):
        self.client = httpx.Client(
            timeout=self.TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

    def validate_eyewear_store(self, url: str) -> dict:
        """
        Validate if a Shopify store primarily sells eyewear products.

        Args:
            url: Shopify store URL

        Returns:
            dict with:
                - is_eyewear_store: bool
                - eyewear_ratio: float (0-1)
                - total_products: int
                - eyewear_products: int
                - rejection_reason: str or None
        """
        result = {
            "is_eyewear_store": False,
            "eyewear_ratio": 0.0,
            "total_products": 0,
            "eyewear_products": 0,
            "rejection_reason": None,
        }

        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            # Fetch products.json
            products_url = urljoin(url, "/products.json")
            response = self.client.get(products_url)

            if response.status_code != 200:
                result["rejection_reason"] = "Cannot access products.json"
                return result

            data = response.json()
            products = data.get("products", [])

            if not products:
                result["rejection_reason"] = "No products found"
                return result

            result["total_products"] = len(products)

            # Analyze each product
            eyewear_count = 0
            non_eyewear_count = 0

            for product in products:
                title = (product.get("title") or "").lower()
                product_type = (product.get("product_type") or "").lower()
                tags = [t.lower() for t in product.get("tags", [])]
                vendor = (product.get("vendor") or "").lower()

                combined_text = f"{title} {product_type} {' '.join(tags)} {vendor}"

                # Check for negative keywords (non-eyewear)
                is_negative = any(
                    neg.lower() in combined_text
                    for neg in NEGATIVE_KEYWORDS_EYEWEAR
                )

                if is_negative:
                    non_eyewear_count += 1
                    continue

                # Check for eyewear indicators
                is_eyewear = any(
                    indicator in combined_text
                    for indicator in self.EYEWEAR_INDICATORS
                )

                if is_eyewear:
                    eyewear_count += 1
                else:
                    # Check product type specifically
                    eyewear_types = ["eyewear", "glasses", "sunglasses", "optical"]
                    if any(et in product_type for et in eyewear_types):
                        eyewear_count += 1

            result["eyewear_products"] = eyewear_count

            if result["total_products"] > 0:
                result["eyewear_ratio"] = eyewear_count / result["total_products"]

            # Determine if it's an eyewear store
            if result["eyewear_ratio"] >= self.MIN_EYEWEAR_RATIO:
                result["is_eyewear_store"] = True
                logger.info(
                    f"✓ Eyewear store validated: {eyewear_count}/{result['total_products']} "
                    f"products ({result['eyewear_ratio']:.0%})"
                )
            else:
                result["rejection_reason"] = (
                    f"Only {result['eyewear_ratio']:.0%} eyewear products "
                    f"(minimum {self.MIN_EYEWEAR_RATIO:.0%} required)"
                )
                logger.warning(f"✗ Not an eyewear store: {result['rejection_reason']}")

        except Exception as e:
            result["rejection_reason"] = f"Error analyzing products: {str(e)}"
            logger.warning(f"Product validation error: {e}")

        return result

    def get_product_categories(self, url: str) -> list[str]:
        """
        Get unique product categories/types from a store.

        Args:
            url: Shopify store URL

        Returns:
            List of product types found
        """
        categories = set()

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            products_url = urljoin(url, "/products.json")
            response = self.client.get(products_url)

            if response.status_code == 200:
                data = response.json()
                for product in data.get("products", []):
                    product_type = product.get("product_type")
                    if product_type:
                        categories.add(product_type)

        except Exception as e:
            logger.debug(f"Error getting product categories: {e}")

        return list(categories)

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
