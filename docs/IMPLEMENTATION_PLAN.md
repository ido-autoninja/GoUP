# Implementation Plan

## Phase 1: Project Setup

### Step 1.1: Environment Setup
- [ ] Create Python virtual environment
- [ ] Set up project structure (src/, tests/, config/, data/)
- [ ] Create requirements.txt with initial dependencies
- [ ] Set up environment variables configuration (.env)
- [ ] Create .gitignore for Python projects

### Step 1.2: Configuration Module
- [ ] Create config loader for API keys and settings
- [ ] Set up logging configuration
- [ ] Create constants file (keywords, countries, exclusions)

---

## Phase 2: Data Collection Layer

### Step 2.1: Shopify Store Discovery
- [ ] Integrate Apify Shopify Store Finder API
- [ ] Implement keyword-based search (pharmacy, sunglasses, eyewear, etc.)
- [ ] Add geographic filtering (US, EU countries)
- [ ] Store raw results in structured format

### Step 2.2: Shopify Platform Verification
- [ ] Create Shopify detection module
- [ ] Check `/products.json` endpoint
- [ ] Detect Shopify CDN URLs in page source
- [ ] Verify store is active and has products

### Step 2.3: E-Pharmacy Data Collection
- [ ] Research epharmacydata.com API/scraping options
- [ ] Implement e-pharmacy list compilation
- [ ] Cross-reference with Shopify verification

---

## Phase 3: Enrichment Layer

### Step 3.1: Company Enrichment
- [ ] Integrate Apify LinkedIn Company Scraper
- [ ] Extract: company size, industry, location, description
- [ ] Match companies to their LinkedIn profiles
- [ ] Store enriched company data

### Step 3.2: Decision Maker Identification
- [ ] Integrate Apify LinkedIn Employees Scraper
- [ ] Filter by target titles (CEO, Founder, Owner, BD Manager, E-commerce Director)
- [ ] Extract: name, title, LinkedIn URL, location

### Step 3.3: Contact Information
- [ ] Integrate Hunter.io API for email finding
- [ ] Implement email verification
- [ ] Store verified contact information

---

## Phase 4: Lead Scoring & Qualification

### Step 4.1: Scoring Engine
- [ ] Implement scoring algorithm based on PRD criteria:
  - Platform = Shopify (+20)
  - Company size 20-50 (+15) / 51-200 (+10)
  - Target geography (+15)
  - E-commerce presence (+10)
  - No current RX eyewear (+15)
  - Decision maker found (+10)
  - Email verified (+5)
- [ ] Set qualification threshold (≥60)

### Step 4.2: Exclusion Filter
- [ ] Implement exclusion list check (GlassesUSA, Zenni, etc.)
- [ ] Filter out companies already selling prescription eyewear
- [ ] Deduplicate leads

---

## Phase 5: Personalization Layer

### Step 5.1: Research Summary Generation
- [ ] Integrate Claude API or Google Gemini
- [ ] Create prompt templates for company research summaries
- [ ] Generate fit analysis for each lead

### Step 5.2: Outreach Copy Generation
- [ ] Create prompt templates for:
  - LinkedIn connection request (≤300 chars)
  - LinkedIn follow-up message
  - Cold email (subject + body)
- [ ] Generate personalized copy for each qualified lead

---

## Phase 6: Output & Delivery

### Step 6.1: Data Export
- [ ] Integrate Google Sheets API
- [ ] Create output spreadsheet template
- [ ] Implement export function for qualified leads

### Step 6.2: n8n Workflow (Optional)
- [ ] Document workflow for n8n integration
- [ ] Create webhook endpoints if needed

---

## Phase 7: Testing & Validation

### Step 7.1: Unit Tests
- [ ] Test Shopify detection accuracy
- [ ] Test scoring algorithm
- [ ] Test API integrations

### Step 7.2: Pilot Validation
- [ ] Run on 5 sample URLs from client
- [ ] Validate output quality
- [ ] Gather feedback and iterate

---

## Execution Order

**Week 1: Foundation**
1. Project setup (Step 1.1, 1.2)
2. Shopify verification module (Step 2.2)
3. Test on sample URLs

**Week 2: Data Collection**
4. Apify integrations (Step 2.1, 3.1, 3.2)
5. Hunter.io integration (Step 3.3)
6. Scoring engine (Step 4.1, 4.2)

**Week 3: Personalization & Output**
7. AI copy generation (Step 5.1, 5.2)
8. Google Sheets export (Step 6.1)
9. End-to-end testing on pilot leads

---

## File Structure (Planned)

```
GoUP/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config.py               # Configuration loader
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── shopify_finder.py   # Apify Shopify integration
│   │   ├── shopify_verifier.py # Platform verification
│   │   └── epharmacy.py        # E-pharmacy data
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── linkedin.py         # LinkedIn company/people
│   │   └── email_finder.py     # Hunter.io integration
│   ├── scoring/
│   │   ├── __init__.py
│   │   └── lead_scorer.py      # Scoring algorithm
│   ├── personalization/
│   │   ├── __init__.py
│   │   ├── research.py         # Company research
│   │   └── copywriter.py       # Outreach copy generation
│   └── export/
│       ├── __init__.py
│       └── sheets.py           # Google Sheets export
├── tests/
├── config/
│   └── prompts/                # AI prompt templates
├── data/
│   ├── raw/                    # Raw scraped data
│   ├── enriched/               # Enriched leads
│   └── output/                 # Final qualified leads
├── docs/
├── .env.example
├── requirements.txt
└── README.md
```
