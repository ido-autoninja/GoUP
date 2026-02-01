"""Constants and configuration values for GoUP."""

# Target Countries (ISO codes + common variations)
TARGET_COUNTRIES = [
    "US", "USA",  # United States
    "UK", "GB",   # United Kingdom
    "IE",         # Ireland
    "DE",         # Germany
    "AT",         # Austria
    "CH",         # Switzerland
    "FR",         # France
    "NL",         # Netherlands
    "BE",         # Belgium
    "ES",         # Spain
    "IT",         # Italy
    "PT",         # Portugal
    "FI",         # Finland
    "SE",         # Sweden
    "DK",         # Denmark
    "NO",         # Norway
    "CA",         # Canada
    "AU",         # Australia
]

# Company Size Filters
COMPANY_SIZE_MIN = 10
COMPANY_SIZE_SWEET_SPOT_MIN = 20
COMPANY_SIZE_SWEET_SPOT_MAX = 50
COMPANY_SIZE_MAX = 200

# Exclusion List - Companies to never include
EXCLUSION_LIST = [
    "glassesusa",
    "eyebuydirect",
    "zenni optical",
    "zenni",
    "sunglass hut",
    "lenscrafters",
    "warby parker",
    "specsavers",
    "fielmann",
    "apollo optik",
]

# Keywords for Shopify Store Discovery
KEYWORDS_EPHARMACY = {
    "en": ["pharmacy", "drugstore", "chemist", "health store"],
    "de": ["apotheke", "online apotheke", "versandapotheke"],
    "fr": ["pharmacie", "parapharmacie"],
    "es": ["farmacia", "parafarmacia"],
    "nl": ["apotheek", "drogist"],
    "it": ["farmacia", "parafarmacia"],
    "fi": ["apteekki"],
}

KEYWORDS_EYEWEAR = [
    "prescription glasses online",
    "eyeglasses store",
    "sunglasses shop",
    "optical store online",
    "buy eyewear online",
    "designer eyeglasses",
    "reading glasses store",
    "blue light glasses",
    "eyewear boutique",
    "rx sunglasses",
    "prescription sunglasses",
    "optical frames store",
]

NEGATIVE_KEYWORDS_EYEWEAR = [
    "picture frame",
    "photo frame",
    "wine glass",
    "drinking glass",
    "window glass",
    "art frame",
    "poster frame",
    "mirror frame",
    "glassware",
    "stemware",
]

# Target Decision Maker Titles
TARGET_TITLES = [
    "CEO",
    "Chief Executive Officer",
    "Founder",
    "Co-Founder",
    "Owner",
    "Managing Director",
    "Business Development",
    "E-commerce Director",
    "Ecommerce Director",
    "E-Commerce Manager",
    "Head of E-commerce",
    "Director of Business Development",
]

# Lead Scoring Points
SCORING_WEIGHTS = {
    "platform_shopify": 20,
    "company_size_sweet_spot": 15,  # 20-50 employees
    "company_size_good": 10,  # 51-200 employees
    "target_geography": 15,
    "ecommerce_presence": 10,
    "no_rx_eyewear": 15,
    "decision_maker_found": 10,
    "email_verified": 5,
}

# Qualification Threshold
QUALIFICATION_THRESHOLD = 50

# Apify Actor IDs
APIFY_ACTORS = {
    "shopify_store_finder": "canadesk/shopify-store-finder",
    "shopify_store_info": "drobnikj/shopify-store-info",
    "linkedin_company": "logical_scrapers/linkedin-company-scraper",
    "linkedin_employees": "caprolok/linkedin-employees-scraper",
    "google_search": "apify/google-search-scraper",
}

# Sample URLs for Testing
SAMPLE_URLS = [
    {"url": "ashford.com/collections/sunglasses", "segment": "sunglasses", "priority": "high"},
    {"url": "iron.paris", "segment": "sunglasses", "priority": "medium"},
    {"url": "apteekki360.fi", "segment": "e-pharmacy", "priority": "high"},
    {"url": "galileofarma.com", "segment": "e-pharmacy", "priority": "high"},
    {"url": "doktorabc.com/de", "segment": "e-pharmacy", "priority": "high"},
]
