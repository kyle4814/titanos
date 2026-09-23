"""Canonical global opportunity scope for TitanOS.

This is a coverage taxonomy, not a list of currently discovered opportunities.
It is intentionally broad so source adapters can declare what they cover and
the radar can identify blind spots.

New categories should extend this registry rather than creating parallel
opportunity vocabularies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "OPPORTUNITY_SCOPE_VERSION",
    "OPPORTUNITY_DOMAINS",
    "OPPORTUNITY_TYPES",
    "OPPORTUNITY_SIGNALS",
    "OPPORTUNITY_GEOGRAPHIES",
    "OPPORTUNITY_CHANNELS",
    "OPPORTUNITY_SCOPE",
    "OpportunityScope",
]

OPPORTUNITY_SCOPE_VERSION: Final[str] = "global-v1"

# Domain -> opportunity families. Keep values stable: adapters may persist them.
OPPORTUNITY_DOMAINS: Final[dict[str, tuple[str, ...]]] = {
    "security": (
        "bug_bounty", "vulnerability_disclosure", "security_research",
        "penetration_testing", "security_audit", "ctf", "security_grant",
        "incident_response", "threat_intelligence", "security_contract",
    ),
    "software_engineering": (
        "open_source_issue", "paid_open_source", "software_project",
        "software_contract", "maintenance", "refactoring", "integration",
        "api_integration", "plugin", "extension", "sdk", "developer_program",
    ),
    "web3": (
        "protocol_grant", "ecosystem_grant", "smart_contract_audit",
        "smart_contract_bounty", "blockchain_security", "hackathon",
        "protocol_integration", "developer_reward", "governance_proposal",
    ),
    "ai_data_research": (
        "ai_challenge", "ml_competition", "dataset", "data_contract",
        "data_annotation", "research_call", "research_grant",
        "research_collaboration", "benchmark", "forecasting",
        "scientific_challenge", "compute_grant",
    ),
    "government_public_sector": (
        "tender", "rfp", "rfq", "rft", "eoi", "procurement",
        "supplier_panel", "standing_offer", "government_contract",
        "public_grant", "challenge_prize", "concession", "license",
    ),
    "commercial_sales": (
        "customer_lead", "sales_signal", "rfp_response", "vendor_request",
        "supplier_request", "channel_partner", "reseller", "distributor",
        "white_label", "agency_contract", "consulting_contract",
        "professional_services", "outsourcing",
    ),
    "capital": (
        "angel_investment", "venture_capital", "family_office",
        "corporate_venture", "private_equity", "venture_debt",
        "revenue_based_finance", "crowdfunding", "syndicate",
        "accelerator", "incubator", "startup_program", "pitch_competition",
    ),
    "grants_and_nonprofit": (
        "corporate_grant", "foundation_grant", "philanthropic_grant",
        "nonprofit_grant", "community_grant", "social_impact",
        "fellowship", "scholarship", "prize_funding",
    ),
    "innovation_competition": (
        "hackathon", "innovation_challenge", "open_innovation",
        "design_challenge", "engineering_challenge", "entrepreneurship_prize",
        "startup_competition", "idea_competition",
    ),
    "employment_and_gig": (
        "job", "contract_role", "freelance_project", "consulting_role",
        "temporary_work", "remote_role", "expert_network", "task_marketplace",
        "creator_contract",
    ),
    "partnerships_and_ecosystems": (
        "strategic_partnership", "technology_partnership", "integration_partner",
        "referral_partner", "affiliate", "sponsorship", "community_partner",
        "platform_partner", "marketplace_partner", "co_marketing",
    ),
    "marketplaces_and_digital_assets": (
        "saas_acquisition", "website_acquisition", "domain", "app",
        "plugin_marketplace", "template", "digital_product", "newsletter",
        "community", "api_product", "data_product", "content_asset",
        "intellectual_property", "license",
    ),
    "real_world_commerce": (
        "manufacturing", "contract_manufacturing", "wholesale",
        "distribution", "logistics", "import_export", "supplier",
        "franchise", "retail", "ecommerce", "construction",
        "maintenance", "facilities", "energy", "telecommunications",
    ),
    "finance_and_markets": (
        "financial_service", "fintech_partnership", "banking_product",
        "payments", "insurance", "trade_finance", "market_data",
        "research_bounty", "marketplace_listing",
    ),
    "health_and_life_science": (
        "healthcare_contract", "clinical_research", "life_science_grant",
        "biotech_partnership", "medical_research", "health_innovation",
    ),
    "climate_and_environment": (
        "climate_grant", "carbon_project", "renewable_energy",
        "environmental_contract", "sustainability_program",
        "circular_economy", "conservation",
    ),
    "education": (
        "education_contract", "edtech_partnership", "course_contract",
        "training_contract", "academic_fellowship", "student_competition",
    ),
    "media_and_creative": (
        "content_contract", "media_partnership", "licensing",
        "design_project", "creative_commission", "film_media",
        "music_opportunity", "publishing", "creator_program",
    ),
    "property_and_physical_assets": (
        "property", "commercial_property", "lease", "development",
        "equipment", "vehicle", "industrial_asset", "land",
    ),
    "international_development": (
        "multilateral_tender", "development_contract", "international_grant",
        "ngo_procurement", "humanitarian_contract", "development_program",
    ),
    "legal_and_professional": (
        "legal_technology", "professional_services", "expert_witness",
        "expert_network", "compliance_contract", "certification_program",
    ),
    "community_and_civic": (
        "community_project", "civic_challenge", "participatory_grant",
        "local_program", "volunteer_to_paid", "public_consultation",
    ),
    "emerging_frontiers": (
        "robotics", "autonomous_systems", "spatial_computing",
        "quantum", "advanced_manufacturing", "space",
        "drones", "mobility", "future_energy",
    ),
}

OPPORTUNITY_TYPES: Final[tuple[str, ...]] = tuple(
    sorted({item for values in OPPORTUNITY_DOMAINS.values() for item in values})
)

# Observable events that can create candidate opportunities. A signal is never
# promoted to a verified opportunity without evidence.
OPPORTUNITY_SIGNALS: Final[tuple[str, ...]] = (
    "funding_raised", "funding_announced", "new_fund", "product_launch",
    "market_expansion", "new_hire", "hiring_surge", "executive_change",
    "acquisition", "merger", "divestiture", "new_contract",
    "contract_expiry", "procurement_notice", "rfp_published",
    "grant_opened", "program_opened", "bounty_opened", "bounty_changed",
    "security_advisory", "cve_published", "repository_created",
    "repository_archived", "repository_issue", "repository_release",
    "api_released", "partner_program_opened", "hackathon_opened",
    "competition_opened", "dataset_released", "research_call",
    "regulatory_change", "policy_change", "license_change",
    "price_change", "vendor_change", "technology_migration",
    "expansion_announced", "facility_opened", "facility_closed",
    "supplier_needed", "customer_demand", "community_request",
    "job_posting", "expert_request", "asset_listed",
)

# Geography is deliberately represented as a dimension, not a fixed country
# list. Source adapters can attach ISO country/region codes without taxonomy
# churn.
OPPORTUNITY_GEOGRAPHIES: Final[tuple[str, ...]] = (
    "global", "multilateral", "regional", "national", "state_province",
    "territory", "local", "cross_border", "remote",
)

OPPORTUNITY_CHANNELS: Final[tuple[str, ...]] = (
    "government_portal", "procurement_portal", "grant_portal",
    "security_program", "bug_bounty_platform", "github",
    "open_source_foundation", "research_portal", "competition_platform",
    "marketplace", "job_board", "company_website", "investor_portal",
    "accelerator", "community", "professional_network", "news",
    "public_registry", "regulatory_registry", "api_directory",
    "ecosystem_portal", "blockchain_protocol", "social_platform",
    "email", "referral", "direct_request", "web_discovery",
)


@dataclass(frozen=True)
class OpportunityScope:
    """Coverage contract used by the radar and source adapters."""

    version: str
    domains: tuple[str, ...]
    opportunity_types: tuple[str, ...]
    signals: tuple[str, ...]
    geographies: tuple[str, ...]
    channels: tuple[str, ...]

    @classmethod
    def global_default(cls) -> "OpportunityScope":
        return cls(
            version=OPPORTUNITY_SCOPE_VERSION,
            domains=tuple(sorted(OPPORTUNITY_DOMAINS)),
            opportunity_types=OPPORTUNITY_TYPES,
            signals=OPPORTUNITY_SIGNALS,
            geographies=OPPORTUNITY_GEOGRAPHIES,
            channels=OPPORTUNITY_CHANNELS,
        )

    def contains_type(self, opportunity_type: str) -> bool:
        return opportunity_type in self.opportunity_types

    def blind_spots(
        self,
        *,
        covered_types: set[str],
        covered_channels: set[str],
    ) -> dict[str, tuple[str, ...]]:
        return {
            "opportunity_types": tuple(
                item for item in self.opportunity_types if item not in covered_types
            ),
            "channels": tuple(
                item for item in self.channels if item not in covered_channels
            ),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "domains": self.domains,
            "opportunity_types": self.opportunity_types,
            "signals": self.signals,
            "geographies": self.geographies,
            "channels": self.channels,
        }


OPPORTUNITY_SCOPE: Final[OpportunityScope] = OpportunityScope.global_default()
