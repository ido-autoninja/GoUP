"""AI-powered personalized copy generation using Google Gemini."""

from typing import Optional

import google.generativeai as genai
from loguru import logger

from ..config import get_settings
from ..models import Lead, OutreachCopy, Segment


# GoHub Business Context for Outreach Generation
GOHUB_CONTEXT = """
## About GoHub (GoOptichub)

GoHub is a B2B SaaS platform providing a plug-and-play vision care solution for e-commerce businesses. We enable online stores to add prescription eyewear capabilities to their existing product catalog without traditional complexities.

## The Problem We Solve

E-commerce stores face significant barriers selling prescription eyewear:
- Inventory Complexity - Need thousands of lens combinations
- Lab Integrations - Must partner with optical laboratories
- Regulatory Hurdles - Prescription eyewear is regulated, requiring licenses
- Technical Knowledge - Staff needs optical expertise
- High Capital Investment - Upfront costs for inventory, equipment, training

## The Market Opportunity

- **60% of the eyewear market is prescription-based** - stores selling only non-prescription eyewear miss the majority of the market
- E-pharmacies already serve health-conscious customers who likely need vision correction
- Sunglasses brands have existing frame inventory that could generate additional revenue with prescription lenses

## The GoHub Solution

1. **Prescription Add-On Module** - Customers add prescription lenses to any frame
2. **Virtual Try-On Technology** - AI-powered, works with any device camera
3. **360° Product Modeling** - High-quality 3D visualization
4. **AI Optician** - Intelligent assistant guiding customers through prescription buying
5. **Back-End Fulfillment** - We handle labs, manufacturing, quality control, regulatory compliance

### Integration
- Timeline: Days, not months
- Technical Effort: Minimal - plug-and-play
- Platform Support: Shopify (primary), custom platforms

## Value Propositions

### For E-Pharmacies
"You're already in healthcare. Adding eye care is a natural extension. Your customers trust you for their health needs - now serve their vision needs too."
- Expand product catalog without inventory investment
- Serve existing customers' unmet needs
- Increase average order value
- Differentiate from competitors

### For Sunglasses/Frames Retailers
"Your frames are already beautiful. Now make them accessible to the 60% of customers who need prescription lenses."
- Unlock 60% more of the addressable market
- Increase revenue from existing inventory
- No need to change suppliers or designs
- Higher margins on prescription orders

## Why GoHub vs. Building In-House

| Factor | In-House | GoHub |
|--------|----------|-------|
| Time to market | 6-12 months | Days |
| Upfront investment | €100K+ | Minimal |
| Lab partnerships | You negotiate | Included |
| Regulatory compliance | Your responsibility | Handled |
| Risk | High | Low |

## Messaging Guidelines

### Tone
- Professional but approachable
- Confident without being pushy
- Focus on business value, not technical features
- Speak to their business goals

### Key Messages to Emphasize
1. "60% of the eyewear market is prescription" - the hook
2. "Days, not months" - speed of implementation
3. "No inventory, no labs, no complexity" - remove barriers
4. "Use your existing collection" - no changes needed
5. "Plug-and-play" - technical simplicity

### Messages to Avoid
- Don't oversell or make unrealistic promises
- Don't use too much technical jargon
- Don't criticize their current business model
- Don't be generic - always personalize

## The Ask
- A brief call or demo (15-30 minutes)
- Show how GoHub could work with their specific store
- No commitment required - just exploration
"""


class Copywriter:
    """Generate personalized outreach copy using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        settings = get_settings()
        genai.configure(api_key=api_key or settings.google_api_key)
        self.model = genai.GenerativeModel(model)

    def _get_segment_context(self, lead: Lead) -> str:
        """Get segment-specific messaging context."""
        segment = lead.company.segment

        if segment == Segment.EPHARMACY:
            return """
SEGMENT: E-Pharmacy / Online Drugstore

ANGLE: "You're already in healthcare. Adding eye care is a natural extension."

KEY POINTS:
- Their customers already trust them for health needs
- Vision care is a natural category extension
- 60% of adults need prescription eyewear
- No need to become opticians - GoHub handles complexity
- Increase customer lifetime value by serving more needs

TONE: Healthcare-focused, trust-building, expansion opportunity
"""
        else:  # EYEWEAR, SUNGLASSES
            return """
SEGMENT: Eyewear / Sunglasses Brand

ANGLE: "Your frames are stunning. But you're only reaching 40% of potential customers."

KEY POINTS:
- They're missing 60% of the market (prescription wearers)
- Their existing frames can become prescription-ready
- No inventory changes needed
- Premium positioning with prescription capability
- Higher margins on prescription orders

TONE: Fashion-forward, revenue opportunity, market expansion
"""

    def generate_outreach(self, lead: Lead) -> OutreachCopy:
        """
        Generate personalized outreach copy for a lead.

        Args:
            lead: Lead object with company and decision maker info

        Returns:
            OutreachCopy object with all generated content
        """
        company = lead.company
        dm = lead.decision_maker

        logger.info(f"Generating outreach copy for: {company.name}")

        # Generate research summary
        research_summary = self._generate_research_summary(lead)

        # Generate LinkedIn connection request
        linkedin_request = self._generate_linkedin_request(lead)

        # Generate LinkedIn follow-up
        linkedin_followup = self._generate_linkedin_followup(lead)

        # Generate cold email
        email_subject, email_body = self._generate_cold_email(lead)

        outreach = OutreachCopy(
            research_summary=research_summary,
            linkedin_connection_request=linkedin_request,
            linkedin_followup=linkedin_followup,
            email_subject=email_subject,
            email_body=email_body,
        )

        lead.outreach = outreach
        return outreach

    def _generate_research_summary(self, lead: Lead) -> str:
        """Generate a research summary for the lead."""
        company = lead.company
        segment_context = self._get_segment_context(lead)

        prompt = f"""You are a sales researcher at GoHub. Write a brief research summary (3-4 sentences) for the sales team.

{GOHUB_CONTEXT}

{segment_context}

TARGET COMPANY:
- Company: {company.name}
- Website: {company.website}
- Industry: {company.industry or company.segment or 'E-commerce'}
- Country: {company.country or 'Unknown'}
- Size: {company.employee_count or 'Unknown'} employees
- Description: {company.description or 'No description available'}

INCLUDE:
1. What the company does (be specific based on their description)
2. Why they would benefit from GoHub (use segment-specific angle)
3. Potential challenges or objections they might have

Keep it factual, concise, actionable. No fluff. No generic statements."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating research summary: {e}")
            return f"{company.name} is an e-commerce company that could benefit from expanding into prescription eyewear with GoHub's plug-and-play solution."

    def _generate_linkedin_request(self, lead: Lead) -> str:
        """Generate LinkedIn connection request (max 300 chars)."""
        company = lead.company
        dm = lead.decision_maker
        dm_name = dm.name.split()[0] if dm and dm.name != "Store Contact" else "there"
        segment_context = self._get_segment_context(lead)

        prompt = f"""You are an SDR at GoHub. Write a LinkedIn connection request.

{GOHUB_CONTEXT}

{segment_context}

RECIPIENT:
- Name: {dm_name}
- Company: {company.name}
- Industry: {company.industry or company.segment or 'e-commerce'}
- Country: {company.country or 'Europe/US'}
- Description: {company.description or 'E-commerce store'}

STRICT REQUIREMENTS:
- MAXIMUM 300 characters (this is a LinkedIn limit - MUST be under 300)
- Start with "Hi {dm_name},"
- Reference something SPECIFIC about their business (use their description)
- Hint at the value proposition without being salesy
- End with a soft, curiosity-driven question or statement
- DO NOT use "60%" statistic in the connection request (save for follow-up)
- Be conversational, not corporate

Output ONLY the message text. Nothing else. No quotes."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip().strip('"').strip("'")
            # Ensure it's under 300 chars
            if len(text) > 300:
                text = text[:297] + "..."
            return text
        except Exception as e:
            logger.error(f"Error generating LinkedIn request: {e}")
            return f"Hi {dm_name}, love what {company.name} is building! We help e-commerce brands add prescription eyewear capability without the complexity. Would love to connect and share ideas."

    def _generate_linkedin_followup(self, lead: Lead) -> str:
        """Generate LinkedIn follow-up message."""
        company = lead.company
        dm = lead.decision_maker
        dm_name = dm.name.split()[0] if dm and dm.name != "Store Contact" else "there"
        segment_context = self._get_segment_context(lead)

        prompt = f"""You are an SDR at GoHub. Write a LinkedIn follow-up message after they accepted your connection.

{GOHUB_CONTEXT}

{segment_context}

RECIPIENT:
- Name: {dm_name}
- Company: {company.name}
- Industry: {company.industry or company.segment or 'e-commerce'}
- Country: {company.country or 'Europe/US'}
- Description: {company.description or 'E-commerce store'}

REQUIREMENTS:
- Thank them for connecting (brief, not overly grateful)
- NOW introduce the 60% market opportunity naturally
- Explain GoHub's value in one clear sentence
- Use segment-specific messaging
- Suggest a brief call (15-20 minutes) - position as exploring fit, not selling
- Keep it under 500 characters
- Be conversational, peer-to-peer, not salesy
- End with a question that's easy to say yes to

Output ONLY the message text. Nothing else. No quotes."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().strip('"').strip("'")
        except Exception as e:
            logger.error(f"Error generating LinkedIn follow-up: {e}")
            return f"Thanks for connecting, {dm_name}! Quick thought - 60% of the eyewear market is prescription-based. GoHub helps brands like {company.name} tap into that market without inventory or lab complexity. Worth a quick chat to see if there's a fit?"

    def _generate_cold_email(self, lead: Lead) -> tuple[str, str]:
        """Generate cold email subject and body."""
        company = lead.company
        dm = lead.decision_maker
        dm_name = dm.name.split()[0] if dm and dm.name != "Store Contact" else "there"
        dm_title = dm.title if dm and dm.title else "Decision Maker"
        segment_context = self._get_segment_context(lead)

        prompt = f"""You are an SDR at GoHub. Write a cold outreach email.

{GOHUB_CONTEXT}

{segment_context}

RECIPIENT:
- Name: {dm_name}
- Title: {dm_title}
- Company: {company.name}
- Website: {company.website}
- Industry: {company.industry or company.segment or 'e-commerce'}
- Country: {company.country or 'Europe/US'}
- Description: {company.description or 'E-commerce store'}

EMAIL REQUIREMENTS:

SUBJECT LINE:
- Under 50 characters
- Personalized to their company
- Creates curiosity without being clickbait
- No spam trigger words (FREE, ACT NOW, etc.)

BODY:
- Opening: Reference something SPECIFIC about their business (use description)
- Problem/Opportunity: Introduce the 60% market opportunity naturally
- Solution: GoHub in ONE clear sentence (plug-and-play prescription capability)
- Credibility: Brief mention it's days to implement, no inventory/labs needed
- CTA: Suggest a brief demo (15-20 min) to see how it would work on THEIR site
- Closing: Professional but warm

STYLE:
- Under 150 words total
- Short paragraphs (2-3 sentences max)
- No jargon
- Peer-to-peer tone, not vendor-to-customer
- No excessive enthusiasm or exclamation marks

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
SUBJECT: [subject line]
BODY:
[email body]

Sign off with just "Best," and a placeholder [Your Name]."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Parse subject and body
            if "SUBJECT:" in text and "BODY:" in text:
                parts = text.split("BODY:")
                subject = parts[0].replace("SUBJECT:", "").strip()
                body = parts[1].strip()
            else:
                # Fallback parsing
                lines = text.split("\n")
                subject = lines[0] if lines else f"Quick question about {company.name}"
                body = "\n".join(lines[1:]) if len(lines) > 1 else text

            return subject, body

        except Exception as e:
            logger.error(f"Error generating cold email: {e}")
            subject = f"Quick idea for {company.name}"
            body = f"""Hi {dm_name},

Noticed {company.name}'s impressive eyewear collection. Quick question - have you considered adding prescription lenses?

60% of the eyewear market is prescription-based. GoHub helps brands like yours tap into that market in days - no inventory, labs, or complexity.

Would you be open to a 15-minute call to see how this could work for {company.name}?

Best,

[Your Name]"""
            return subject, body

    def generate_batch(self, leads: list[Lead]) -> list[Lead]:
        """Generate outreach copy for multiple leads."""
        for lead in leads:
            if lead.qualification.qualified:
                self.generate_outreach(lead)
        return leads
