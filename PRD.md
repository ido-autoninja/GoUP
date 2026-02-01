# PRD: GoHub Lead Generation System

## Project Overview

### Client
**GoHub (GoOptichub)** - A plug-and-play vision care platform that enables e-commerce brands to add prescription lenses to their existing frames and sunglasses without inventory, lab integrations, or regulatory complexity.

### Business Context
GoHub is an early-stage startup with 6 clients (mostly from connections). They have one SDR based in the Canary Islands who does cold calling. They need to warm up leads before the SDR reaches out, and scale their lead generation efforts.

### Project Goal
Build an automated lead generation system that identifies, enriches, and prepares personalized outreach for potential GoHub customers.

### Pilot Phase Goal
Deliver 5-10 high-quality prospects to prove the concept before scaling to a full system.

---

## Target Audience (ICP - Ideal Customer Profile)

### Primary Segments

#### Segment A: E-Pharmacies / Drugstores
- Online pharmacies with e-commerce presence
- Sell health/wellness products online
- Have existing customer base interested in health products
- **Why they're ideal**: Already in healthcare, easy to add eye care

#### Segment B: Non-RX Eyewear Companies
- Sell sunglasses, frames, readers (no prescription)
- Fashion-forward brands
- Have existing frame inventory
- **Why they're ideal**: Already have the product, just need to add prescription capability

### Firmographic Filters

| Criteria | Specification |
|----------|---------------|
| **Geography** | Europe (EU) + United States |
| **Platform** | Shopify (primary) or Custom-built |
| **Company Size** | 20-50 employees (sweet spot), up to 500 max |
| **Revenue** | SMB to Mid-market |

### Exclusions
- Large enterprises: GlassesUSA, EyeBuyDirect, Zenni Optical, Sunglass Hut, LensCrafters
- Traditional optical chains
- Companies already selling prescription eyewear

### Decision Makers (Personas)
1. **Owner/Founder** - Primary target
2. **CEO/Managing Director** - Primary target
3. **Business Development Manager** - Secondary target
4. **E-commerce Director** - Secondary target

---

## Functional Requirements

### Phase 1: Data Collection

#### 1.1 Shopify Store Discovery
**Input**: Keywords, geographic filters
**Process**:
- Search for Shopify stores by niche keywords
- Keywords for Segment A: "pharmacy", "drugstore", "health store", "wellness", "apotheke", "farmacia", "apotheek"
- Keywords for Segment B: "sunglasses", "eyewear", "frames", "optical", "glasses"
- Filter by geography (US, UK, DE, FR, NL, BE, ES, IT, FI, etc.)

**Output per store**:
- Store URL
- Store name
- Contact email (if available)
- Description
- Product count estimate
- Country/Region

#### 1.2 E-Pharmacy Database
**Sources**:
- epharmacydata.com (2,200+ e-pharmacies globally)
- EAEP members list (European Association of E-Pharmacies)
- EU official pharmacy registries per country
- Manual research of known e-pharmacies

**Process**:
- Compile list of e-pharmacies in target geographies
- Check if they have Shopify or custom platform
- Filter out those already selling prescription eyewear

#### 1.3 Platform Verification
**For each potential lead**:
- Verify if running on Shopify
- Methods:
  - Check for `/products.json` endpoint
  - Look for Shopify CDN URLs
  - Use BuiltWith/Wappalyzer detection
  - Check page source for Shopify indicators

### Phase 2: Company Enrichment

#### 2.1 Company Data
**For each verified Shopify store**:
- Find LinkedIn company page
- Extract:
  - Company size (employee count)
  - Industry classification
  - Headquarters location
  - Company description
  - Website
  - Founded year

#### 2.2 Decision Maker Identification
**For each company**:
- Search LinkedIn for employees
- Filter by titles: CEO, Founder, Owner, Managing Director, Business Development, E-commerce Director
- Extract:
  - Full name
  - Job title
  - LinkedIn profile URL
  - Location
  - Time in role

#### 2.3 Contact Information
**For each decision maker**:
- Find business email (using Hunter.io, Snov.io, or similar)
- Verify email validity
- Find direct phone if available

### Phase 3: Lead Scoring & Qualification

#### Scoring Criteria (0-100 points)

| Criteria | Points | Description |
|----------|--------|-------------|
| Platform = Shopify | +20 | Must-have for pilot |
| Company size 20-50 | +15 | Sweet spot |
| Company size 51-200 | +10 | Good fit |
| In target geography | +15 | US or EU |
| Has e-commerce presence | +10 | Active online store |
| No current RX eyewear | +15 | Not a competitor |
| Decision maker found | +10 | Have contact info |
| Email verified | +5 | Can reach them |

**Qualification Threshold**: Score ≥ 60 = Qualified Lead

### Phase 4: Personalization & Outreach Prep

#### 4.1 Research Summary
**For each qualified lead, compile**:
- Company overview (2-3 sentences)
- Current product offering
- Potential fit with GoHub (why they'd benefit)
- Any recent news/updates about the company
- Potential objections/challenges

#### 4.2 Personalized Outreach Copy
**Generate for each lead**:

**LinkedIn Connection Request** (300 char max):
- Reference something specific about their business
- Mention the value prop briefly
- Soft CTA

**LinkedIn Follow-up Message** (if connected):
- Expand on value proposition
- Include relevant stat (60% of eyewear market is prescription)
- Suggest brief call

**Cold Email**:
- Subject line (personalized)
- Opening hook (reference their business)
- Value proposition (how GoHub helps)
- Social proof (if available)
- CTA (schedule demo)

---

## Technical Architecture

### Data Flow
```
[Data Sources] → [Collection Layer] → [Enrichment Layer] → [Scoring] → [Output]
     ↓                   ↓                   ↓               ↓           ↓
  Apify APIs         Raw Leads          Enriched         Qualified    CRM/Sheet
  Databases          Storage            Leads            Leads        + Copy
```

### Technology Stack

#### Scraping & Data Collection
- **Apify** - Primary scraping platform
  - Shopify Store Finder
  - Shopify Store Info
  - LinkedIn Company Scraper
  - LinkedIn Employees Scraper
- **Custom scrapers** - For specific e-pharmacy directories

#### Automation & Orchestration
- **n8n** - Workflow automation (client's preference)
- Alternative: Make.com

#### AI & Personalization
- **Claude API** or **Google Gemini** - For generating personalized copy
- Prompt templates for consistent output

#### Data Storage
- **Google Sheets** - For pilot phase (simple, shareable)
- **Airtable** - If more structure needed
- **PostgreSQL** - For production scale

#### Email Verification
- **Hunter.io** or **Snov.io** or **NeverBounce**

### API Integrations Required

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| Apify | Shopify & LinkedIn scraping | $49+/mo |
| Hunter.io | Email finding & verification | $49+/mo |
| Claude/Gemini API | Copy generation | ~$20/mo |
| epharmacydata.com | E-pharmacy database | TBD |

---

## Output Specifications

### Lead Database Schema

```json
{
  "lead_id": "string",
  "company": {
    "name": "string",
    "website": "string",
    "shopify_url": "string",
    "platform": "shopify|custom",
    "industry": "e-pharmacy|sunglasses|eyewear",
    "country": "string",
    "employee_count": "number",
    "linkedin_url": "string",
    "description": "string"
  },
  "decision_maker": {
    "name": "string",
    "title": "string",
    "linkedin_url": "string",
    "email": "string",
    "email_verified": "boolean",
    "phone": "string|null"
  },
  "qualification": {
    "score": "number",
    "qualified": "boolean",
    "fit_notes": "string"
  },
  "outreach": {
    "linkedin_connection_request": "string",
    "linkedin_followup": "string",
    "email_subject": "string",
    "email_body": "string"
  },
  "metadata": {
    "created_at": "datetime",
    "source": "string",
    "status": "new|contacted|responded|qualified|disqualified"
  }
}
```

### Deliverables for Pilot

1. **Google Sheet** with 5-10 qualified leads containing:
   - Company info
   - Decision maker contact
   - Lead score
   - Personalized LinkedIn message
   - Personalized email

2. **n8n Workflow** (documented) that can:
   - Take a list of store URLs
   - Enrich with company data
   - Find decision makers
   - Generate personalized copy

---

## Sample Prospects (from client)

### Sunglasses/Frames Segment
1. **ashford.com/collections/sunglasses** - Luxury accessories retailer
2. **iron.paris** - French eyewear brand (note: may not be Shopify)

### E-Pharmacy Segment
1. **apteekki360.fi** - Finnish online pharmacy
2. **galileofarma.com** - European pharmacy
3. **doktorabc.com/de** - German telehealth + pharmacy

**Action**: Verify platform and research these as first batch.

---

## Value Proposition (for copy generation)

### Key Messages

**The Problem**:
- E-commerce brands are leaving money on the table
- 60% of the eyewear market is prescription-based
- Adding prescription capability is complex (labs, regulations, inventory)

**The Solution**:
- GoHub is plug-and-play: integrate in days, not months
- No inventory needed
- No lab integrations required
- No regulatory complexity
- Full solution: prescription add-on, virtual try-on, 360° modeling, AI Optician

**The Benefit**:
- Unlock access to 60% of eyewear market
- Increase revenue and margins
- Use existing frame collection
- No operational headaches

### Social Proof (if available)
- Number of current integrations
- Customer testimonials
- Revenue increase stats from existing clients

---

## Success Criteria

### Pilot Phase (Current)
- [ ] Deliver 5-10 qualified prospects
- [ ] Each prospect has verified contact info
- [ ] Each prospect has personalized outreach copy
- [ ] Client confirms prospects are relevant

### Phase 2 (If pilot succeeds)
- [ ] Build repeatable n8n workflow
- [ ] Generate 60+ leads per quarter
- [ ] Achieve 10%+ response rate on outreach
- [ ] 4 new Shopify clients onboarded in Q1

---

## Project Timeline

### Pilot Phase: 1-2 Weeks

| Day | Task |
|-----|------|
| 1-2 | Research sample prospects from client |
| 3-4 | Set up Apify scrapers, test on samples |
| 5-6 | Build enrichment workflow |
| 7-8 | Generate personalized copy for 5-10 leads |
| 9-10 | Deliver to client, gather feedback |

### Production Phase: 2-4 Weeks (if approved)
- Week 1: Build full n8n workflow
- Week 2: Scale data collection (100+ leads)
- Week 3: Quality assurance, deduplication
- Week 4: Handoff, training, documentation

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LinkedIn scraping blocked | Can't find decision makers | Use multiple accounts, respect rate limits, backup with manual research |
| Low Shopify adoption in e-pharmacies | Limited lead pool | Expand to custom platforms later, or focus on sunglasses segment |
| Email deliverability issues | Outreach fails | Use warm-up tools, verify all emails, personalize heavily |
| Niche too small | Not enough leads | Expand geography, broaden keywords |
| Decision maker data incomplete | Can't reach right people | Manual LinkedIn research as fallback |

---

## Appendix

### Useful Resources
- Apify Shopify Store Finder: `apify.com/igolaizola/shopify-store-finder`
- Apify LinkedIn Employees Scraper: `apify.com/caprolok/linkedin-employees-scraper`
- E-Pharmacy Database: `epharmacydata.com`
- EAEP Members: `eaep.com/en/`
- Store Leads (Shopify directory): `storeleads.app`

### Keywords for Scraping

**E-Pharmacy (by language)**:
- English: pharmacy, drugstore, chemist, health store
- German: apotheke, online apotheke, versandapotheke
- French: pharmacie, parapharmacie
- Spanish: farmacia, parafarmacia
- Dutch: apotheek, drogist
- Italian: farmacia, parafarmacia
- Finnish: apteekki

**Eyewear**:
- sunglasses, shades, eyewear, frames, optical, glasses, spectacles, readers

### Example Outreach Templates

**LinkedIn Connection Request (English)**:
```
Hi [First Name], I noticed [Company] has an impressive collection of [sunglasses/health products]. We help brands like yours add prescription eyewear capability in days—unlocking 60% more of the market. Would love to connect!
```

**Cold Email Subject Lines**:
- "Quick question about [Company]'s eyewear strategy"
- "[First Name], unlock 60% more revenue from your frames"
- "How [Similar Company] added €X in new revenue"

---

## Notes for Development

1. **Start with the 5 sample URLs** from the client to validate the workflow
2. **Shopify verification is critical** - don't waste time on non-Shopify stores in pilot
3. **Quality over quantity** - 5 perfect leads > 50 mediocre ones
4. **Keep human in the loop** - Don't fully automate outreach in pilot phase
5. **Document everything** - Client may want to own the system later

---

*Document Version: 1.0*
*Created: January 2026*
*Author: AutoNinja*