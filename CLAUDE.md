# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GoUP is an automated lead generation system for GoHub (GoOptichub), a plug-and-play vision care platform. The system identifies Shopify stores in target segments (eyewear, e-pharmacy), enriches them with LinkedIn/email data, scores them for qualification, and generates personalized outreach copy.

## Commands

```bash
# Setup
venv\Scripts\activate  # Windows (or: source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt

# Run pipeline
python -m src.main pilot                           # Process sample URLs from constants.py
python -m src.main pilot --export                  # + Export to Google Sheets
python -m src.main verify https://example.com      # Check if URL is Shopify
python -m src.main process https://store.com       # Process specific URLs
python -m src.main search --segment eyewear --max-results 20

# Verbose mode
python -m src.main pilot -v

# Testing
pytest                         # Run all tests
pytest tests/test_file.py      # Run specific test file
pytest -k "test_name"          # Run tests matching pattern

# Linting
ruff check src/                # Lint code
black src/                     # Format code
```

## Architecture

The `LeadGenerationPipeline` in `pipeline.py` orchestrates the 6-step flow:

1. **Verify** (`collectors/shopify_verifier.py`) - Check if URL is Shopify via `/products.json` endpoint and CDN indicators
2. **Enrich Company** (`enrichment/linkedin.py`) - Get company data from LinkedIn via Apify
3. **Find Decision Makers** (`enrichment/linkedin.py`) - Search for CEO/Founder/BD titles
4. **Find Email** (`enrichment/email_finder.py`) - Hunter.io email lookup and verification
5. **Score** (`scoring/lead_scorer.py`) - Calculate qualification score (threshold: 60 points)
6. **Generate Copy** (`personalization/copywriter.py`) - Google Gemini generates outreach messages

Store discovery uses `collectors/google_finder.py` (DuckDuckGoFinder) to search for Shopify stores by segment keywords.

## Data Models

All models in `models.py` use Pydantic:
- `Lead` - Complete record containing Company, DecisionMaker, Qualification, OutreachCopy
- `Company` - Store info with Platform enum (SHOPIFY/CUSTOM/UNKNOWN) and Segment enum
- `Qualification` - Score, qualified status, and scoring breakdown dict
- `OutreachCopy` - LinkedIn connection/followup messages and email content

## Key Configuration

In `constants.py`:
- `TARGET_COUNTRIES` - US + 15 EU countries
- `COMPANY_SIZE_SWEET_SPOT_MIN/MAX` - 20-50 employees (ideal)
- `EXCLUSION_LIST` - Large competitors to skip (Zenni, Warby Parker, etc.)
- `SCORING_WEIGHTS` - Points per criterion (platform=20, geography=15, etc.)
- `QUALIFICATION_THRESHOLD` - 60 points minimum
- `SAMPLE_URLS` - Test URLs for pilot runs

## Environment Variables

Required in `.env`:
- `APIFY_API_TOKEN` - Apify API token
- `HUNTER_API_KEY` - Hunter.io API key
- `GOOGLE_API_KEY` - Google Gemini API key

For Google Sheets export:
- Place OAuth credentials in `config/credentials.json`
- Token auto-saved to `config/token.json` after first auth
