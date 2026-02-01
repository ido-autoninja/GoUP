# Requirements From User

This document lists everything needed from you to make the system work.

---

## 1. API Keys & Credentials

### Required for Pilot

| Service | What I Need | How to Get It | Estimated Cost |
|---------|-------------|---------------|----------------|
| **Apify** | API Token | Sign up at apify.com → Settings → Integrations → API Token | $49+/month |
| **Hunter.io** | API Key | Sign up at hunter.io → API → Copy API key | $49+/month (or free tier: 25 searches/month) |
| **Claude API** or **Google Gemini** | API Key | console.anthropic.com or ai.google.dev | ~$20/month usage |
| **Google Sheets** | Service Account JSON | Google Cloud Console → Create Service Account → Download JSON key | Free |

### Optional (for scaling)

| Service | What I Need | Purpose |
|---------|-------------|---------|
| **Snov.io** | API Key | Alternative/backup for email finding |
| **NeverBounce** | API Key | Additional email verification |
| **epharmacydata.com** | Access/API | E-pharmacy database (if available) |

---

## 2. Google Cloud Setup (for Sheets Export)

To export leads to Google Sheets, I need:

1. **Google Cloud Project** with Sheets API enabled
2. **Service Account** with Editor access
3. **JSON key file** for the service account
4. **Target Google Sheet** shared with the service account email

### Steps:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable "Google Sheets API"
4. Create a Service Account (IAM & Admin → Service Accounts)
5. Generate a JSON key and download it
6. Share your target Google Sheet with the service account email (ends in `@...iam.gserviceaccount.com`)

---

## 3. Apify Actor Subscriptions

The following Apify actors are needed:

| Actor | URL | Purpose |
|-------|-----|---------|
| Shopify Store Finder | `apify.com/igolaizola/shopify-store-finder` | Find Shopify stores by keywords |
| Shopify Store Info | Search on Apify Store | Get store details |
| LinkedIn Company Scraper | Search on Apify Store | Company enrichment |
| LinkedIn Employees Scraper | `apify.com/caprolok/linkedin-employees-scraper` | Find decision makers |

**Note**: Some actors may require separate subscriptions beyond base Apify plan.

---

## 4. Configuration Decisions

Please confirm or adjust these settings:

### Target Countries
```
US, UK, DE, FR, NL, BE, ES, IT, FI, AT, CH, IE, PT, SE, DK, NO
```
Add or remove countries?

### Company Size Range
- Sweet spot: 20-50 employees
- Maximum: 500 employees

Adjust these limits?

### Exclusion List
Companies to always exclude:
- GlassesUSA
- EyeBuyDirect
- Zenni Optical
- Sunglass Hut
- LensCrafters

Add more companies to exclude?

### Lead Score Threshold
Current: ≥60 points to qualify

Adjust threshold?

---

## 5. Sample URLs for Testing

The PRD mentions these sample prospects. Please confirm these are correct:

**Sunglasses/Frames:**
1. ashford.com/collections/sunglasses
2. iron.paris

**E-Pharmacy:**
1. apteekki360.fi
2. galileofarma.com
3. doktorabc.com/de

Any additional URLs to test with?

---

## 6. Output Preferences

### Google Sheet Structure
Do you want the output in:
- [ ] A single sheet with all data
- [ ] Multiple sheets (Companies, Contacts, Outreach Copy)

### Preferred AI for Copy Generation
- [ ] Claude API (Anthropic)
- [ ] Google Gemini
- [ ] Other: ___________

---

## 7. GoHub Marketing Assets

For better personalized outreach, it would help to have:

- [ ] GoHub one-pager or pitch deck (for reference)
- [ ] Existing customer testimonials/case studies
- [ ] Specific stats (e.g., "clients see X% revenue increase")
- [ ] Any existing email/LinkedIn templates that have worked

---

## 8. Access & Accounts

### LinkedIn (for manual verification if needed)
- Will you provide a LinkedIn account for manual lookups, or should the system rely entirely on Apify?

### CRM Integration (Future)
- Do you use any CRM (HubSpot, Salesforce, Pipedrive)?
- Should leads eventually sync to a CRM?

---

## Summary Checklist

**Must Have Before Starting:**
- [ ] Apify API Token
- [ ] Hunter.io API Key
- [ ] Claude or Gemini API Key
- [ ] Google Service Account JSON (for Sheets export)
- [ ] Confirmation on target countries
- [ ] Confirmation on sample URLs

**Nice to Have:**
- [ ] GoHub marketing materials
- [ ] Additional exclusion list entries
- [ ] CRM details for future integration

---

## How to Provide This Information

1. **API Keys**: Create a `.env` file (I'll provide a template) - NEVER commit this to git
2. **Google JSON**: Place in `config/` directory (also gitignored)
3. **Configuration choices**: Reply to this document or update directly

Once I have the required items, I can begin implementation.
