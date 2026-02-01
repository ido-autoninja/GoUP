"""Lead scoring algorithm."""

from loguru import logger

from ..constants import (
    COMPANY_SIZE_MAX,
    COMPANY_SIZE_MIN,
    COMPANY_SIZE_SWEET_SPOT_MAX,
    COMPANY_SIZE_SWEET_SPOT_MIN,
    EXCLUSION_LIST,
    QUALIFICATION_THRESHOLD,
    SCORING_WEIGHTS,
    TARGET_COUNTRIES,
)
from ..models import Lead, Platform, Qualification


class LeadScorer:
    """Score and qualify leads based on defined criteria."""

    def __init__(
        self,
        qualification_threshold: int = QUALIFICATION_THRESHOLD,
        exclusion_list: list[str] = None,
    ):
        self.threshold = qualification_threshold
        self.exclusion_list = [e.lower() for e in (exclusion_list or EXCLUSION_LIST)]

    def score(self, lead: Lead) -> Lead:
        """
        Score a lead and update its qualification status.

        Args:
            lead: Lead object to score

        Returns:
            Lead object with updated qualification
        """
        company = lead.company
        dm = lead.decision_maker

        breakdown = {}
        total_score = 0

        # Check exclusion first
        if self._is_excluded(company.name):
            lead.qualification = Qualification(
                score=0,
                qualified=False,
                fit_notes="Excluded: Company is in exclusion list",
                scoring_breakdown={"excluded": True},
            )
            logger.info(f"Lead {company.name} excluded (in exclusion list)")
            return lead

        # 1. Platform is Shopify (+20)
        if company.platform == Platform.SHOPIFY:
            breakdown["platform_shopify"] = SCORING_WEIGHTS["platform_shopify"]
            total_score += SCORING_WEIGHTS["platform_shopify"]

        # 2. Company size scoring
        if company.employee_count:
            if COMPANY_SIZE_SWEET_SPOT_MIN <= company.employee_count <= COMPANY_SIZE_SWEET_SPOT_MAX:
                # Sweet spot: 20-50 employees (+15)
                breakdown["company_size_sweet_spot"] = SCORING_WEIGHTS["company_size_sweet_spot"]
                total_score += SCORING_WEIGHTS["company_size_sweet_spot"]
            elif COMPANY_SIZE_MIN <= company.employee_count <= COMPANY_SIZE_MAX:
                # Good fit: 10-200 employees (+10)
                breakdown["company_size_good"] = SCORING_WEIGHTS["company_size_good"]
                total_score += SCORING_WEIGHTS["company_size_good"]

        # 3. Target geography (+15)
        if company.country and company.country.upper() in TARGET_COUNTRIES:
            breakdown["target_geography"] = SCORING_WEIGHTS["target_geography"]
            total_score += SCORING_WEIGHTS["target_geography"]

        # 4. E-commerce presence (+10)
        # Assumed true if we found them as a Shopify store
        if company.shopify_url or company.platform == Platform.SHOPIFY:
            breakdown["ecommerce_presence"] = SCORING_WEIGHTS["ecommerce_presence"]
            total_score += SCORING_WEIGHTS["ecommerce_presence"]

        # 5. No current RX eyewear (+15)
        # Default to true unless explicitly flagged
        if not self._sells_prescription_eyewear(company):
            breakdown["no_rx_eyewear"] = SCORING_WEIGHTS["no_rx_eyewear"]
            total_score += SCORING_WEIGHTS["no_rx_eyewear"]

        # 6. Decision maker found (+10)
        if dm and dm.name:
            breakdown["decision_maker_found"] = SCORING_WEIGHTS["decision_maker_found"]
            total_score += SCORING_WEIGHTS["decision_maker_found"]

        # 7. Email verified (+5)
        if dm and dm.email_verified:
            breakdown["email_verified"] = SCORING_WEIGHTS["email_verified"]
            total_score += SCORING_WEIGHTS["email_verified"]

        # Determine qualification
        qualified = total_score >= self.threshold
        fit_notes = self._generate_fit_notes(breakdown, total_score, qualified)

        lead.qualification = Qualification(
            score=total_score,
            qualified=qualified,
            fit_notes=fit_notes,
            scoring_breakdown=breakdown,
        )

        status = "✓ Qualified" if qualified else "✗ Not qualified"
        logger.info(f"Lead {company.name}: {total_score} points - {status}")

        return lead

    def score_batch(self, leads: list[Lead]) -> list[Lead]:
        """Score multiple leads."""
        scored_leads = []
        for lead in leads:
            scored_lead = self.score(lead)
            scored_leads.append(scored_lead)
        return scored_leads

    def filter_qualified(self, leads: list[Lead]) -> list[Lead]:
        """Filter to only qualified leads."""
        return [lead for lead in leads if lead.qualification.qualified]

    def _is_excluded(self, company_name: str) -> bool:
        """Check if company is in exclusion list."""
        name_lower = company_name.lower()
        for excluded in self.exclusion_list:
            if excluded in name_lower:
                return True
        return False

    def _sells_prescription_eyewear(self, company) -> bool:
        """Check if company already sells prescription eyewear."""
        # Check description for prescription-related terms
        if company.description:
            rx_terms = ["prescription", "rx lenses", "optical lenses", "vision care"]
            desc_lower = company.description.lower()
            for term in rx_terms:
                if term in desc_lower:
                    return True
        return False

    def _generate_fit_notes(
        self,
        breakdown: dict,
        total_score: int,
        qualified: bool,
    ) -> str:
        """Generate human-readable fit notes."""
        notes = []

        # Strengths
        strengths = []
        if "platform_shopify" in breakdown:
            strengths.append("Shopify platform")
        if "company_size_sweet_spot" in breakdown:
            strengths.append("ideal company size")
        if "target_geography" in breakdown:
            strengths.append("target geography")
        if "decision_maker_found" in breakdown:
            strengths.append("decision maker identified")

        if strengths:
            notes.append(f"Strengths: {', '.join(strengths)}")

        # Gaps
        gaps = []
        if "platform_shopify" not in breakdown:
            gaps.append("not on Shopify")
        if "decision_maker_found" not in breakdown:
            gaps.append("no decision maker found")
        if "email_verified" not in breakdown:
            gaps.append("email not verified")

        if gaps and not qualified:
            notes.append(f"Gaps: {', '.join(gaps)}")

        return ". ".join(notes) if notes else "Scoring complete"
