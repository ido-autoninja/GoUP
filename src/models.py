"""Data models for GoUP."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Platform(str, Enum):
    SHOPIFY = "shopify"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class Segment(str, Enum):
    EPHARMACY = "e-pharmacy"
    SUNGLASSES = "sunglasses"
    EYEWEAR = "eyewear"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"


class Company(BaseModel):
    """Company information."""

    name: str
    website: str  # Original URL (may be myshopify.com)
    shopify_url: Optional[str] = None
    primary_domain: Optional[str] = None  # Real company domain (for email lookup)
    platform: Platform = Platform.UNKNOWN
    industry: Optional[str] = None
    segment: Optional[Segment] = None
    country: Optional[str] = None
    employee_count: Optional[int] = None
    linkedin_url: Optional[str] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None


class DecisionMaker(BaseModel):
    """Decision maker contact information."""

    name: str
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    email_verified: bool = False
    phone: Optional[str] = None
    location: Optional[str] = None


class Qualification(BaseModel):
    """Lead qualification data."""

    score: int = 0
    qualified: bool = False
    fit_notes: Optional[str] = None
    scoring_breakdown: dict = Field(default_factory=dict)


class OutreachCopy(BaseModel):
    """Personalized outreach content."""

    linkedin_connection_request: Optional[str] = None
    linkedin_followup: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    research_summary: Optional[str] = None


class Lead(BaseModel):
    """Complete lead record."""

    lead_id: str
    company: Company
    decision_maker: Optional[DecisionMaker] = None
    qualification: Qualification = Field(default_factory=Qualification)
    outreach: Optional[OutreachCopy] = None
    status: LeadStatus = LeadStatus.NEW
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class ShopifyStoreInfo(BaseModel):
    """Raw Shopify store information from scraper."""

    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    product_count: Optional[int] = None
    is_shopify: bool = False
