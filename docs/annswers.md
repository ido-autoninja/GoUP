# GoHub Lead Generation - Project Configuration

## Status: ✅ Approved & Ready to Build

---

## 1. API Keys & Credentials

| Service | Status | Notes |
|---------|--------|-------|
| **Apify** | ✅ Have it | API Token ready |
| **Hunter.io** | ✅ Have it | API Key ready |
| **Google Gemini** | ✅ Have it | For copy generation |
| **Google Sheets** | 🔄 OAuth | Use OAuth flow instead of Service Account |

### Google Authentication
- **Method**: OAuth 2.0 (not Service Account)
- **Reason**: Service Account setup issues
- **Implementation**: Use n8n's built-in Google OAuth node

---

## 2. Target Countries

### Full List (Expanded)
```
US, UK, DE, FR, NL, BE, ES, IT, FI, AT, CH, IE, PT, SE, DK, NO
```

**Total: 16 countries**

| Region | Countries |
|--------|-----------|
| North America | US |
| UK & Ireland | UK, IE |
| DACH | DE, AT, CH |
| Nordics | FI, SE, DK, NO |
| Western Europe | FR, NL, BE |
| Southern Europe | ES, IT, PT |

---

## 3. Company Size Filters

| Parameter | Value |
|-----------|-------|
| **Minimum** | 10 employees |
| **Sweet Spot** | 20-50 employees |
| **Maximum** | 200 employees |

---

## 4. Exclusion List

Companies to always exclude from results:

```
- GlassesUSA
- EyeBuyDirect
- Zenni Optical
- Sunglass Hut
- LensCrafters
- Warby Parker
- Specsavers
- Fielmann
- Apollo Optik
```

**Status**: No additional companies to add at this time.

---

## 5. Sample URLs for Testing

| URL | Segment | Priority |
|-----|---------|----------|
| ashford.com/collections/sunglasses | Sunglasses | High |
| iron.paris | Sunglasses | Medium (may not be Shopify) |
| apteekki360.fi | E-Pharmacy | High |
| galileofarma.com | E-Pharmacy | High |
| doktorabc.com/de | E-Pharmacy | High |

---

## 6. Output Configuration

### Format
- **Type**: Google Sheets
- **Structure**: Multiple Sheets

### Sheet Structure

| Sheet Name | Contents |
|------------|----------|
| **Companies** | Company info: name, URL, platform, country, size, industry |
| **Contacts** | Decision makers: name, title, LinkedIn, email |
| **Outreach** | Personalized copy: LinkedIn message, email subject, email body |
| **Status** | Tracking: lead status, notes, dates |

---

## 7. AI Configuration

| Setting | Value |
|---------|-------|
| **Provider** | Google Gemini |
| **Model** | gemini-1.5-pro (or gemini-1.5-flash for speed) |
| **Use Case** | Personalized outreach copy generation |

---

## 8. Data Collection Method

| Source | Method |
|--------|--------|
| **Shopify Stores** | Apify scrapers |
| **LinkedIn Companies** | Apify scrapers |
| **LinkedIn Employees** | Apify scrapers |
| **Email Finding** | Hunter.io API |

**Note**: All data collection through APIs/Apify. No manual LinkedIn research required.

---

## 9. Project Scope

| Parameter | Value |
|-----------|-------|
| **Type** | POC (Proof of Concept) |
| **Target Output** | 5-10 qualified leads |
| **CRM Integration** | Not needed (Sheets is enough) |
| **Automation Level** | Semi-automated (human review before outreach) |

---

## 10. Pending Items

### Need from Client (Niels)

- [ ] GoHub one-pager or pitch deck
- [ ] Customer testimonials / case studies (if available)
- [ ] Specific stats for copy (e.g., "X% revenue increase")
- [ ] Existing SDR templates that worked

### Technical Setup

- [x] Apify API Token
- [x] Hunter.io API Key
- [x] Google Gemini API Key
- [ ] Google OAuth setup in n8n
- [ ] Target Google Sheet created

---

## Quick Reference

```yaml
project: GoHub Lead Generation
type: POC
target_leads: 5-10
segments:
  - e-pharmacies
  - sunglasses/eyewear (non-RX)
platforms:
  - Shopify (primary)
  - Custom (secondary)
geography:
  - US
  - Europe (UK, DE, FR, NL, BE, ES, IT, FI, AT, CH, IE, PT, SE, DK, NO)
company_size:
  min: 10
  sweet_spot: 20-50
  max: 200
tools:
  scraping: Apify
  email_finding: Hunter.io
  ai_copy: Google Gemini
  output: Google Sheets (OAuth)
  automation: n8n
```

---

## Next Steps

1. **Verify sample URLs** - Check if they're on Shopify
2. **Set up Google OAuth** in n8n
3. **Create target Google Sheet** with proper structure
4. **Build n8n workflow** - Phase 1: Data collection
5. **Test with sample URLs** - Validate the flow
6. **Generate first leads** - Deliver to client

---

*Configuration approved: January 2026*
*Ready for development*