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
    "OPPORTUNITY_VALUE_MECHANISMS",
    "OPPORTUNITY_ACTION_CLASSES",
    "OPPORTUNITY_ACCESS_MODELS",
    "OPPORTUNITY_COVERAGE_AXES",
    "OPPORTUNITY_SCOPE",
    "OpportunityScope",
]

OPPORTUNITY_SCOPE_VERSION: Final[str] = "global-v2"

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


# v2 expansion: domains intentionally include ordinary and specialist economic,
# scientific, civic and asset markets so the radar is not biased toward software.
OPPORTUNITY_DOMAINS.update({
    "agriculture_and_food": (
        "agriculture", "agritech", "farming", "livestock", "aquaculture",
        "food_production", "food_distribution", "food_service", "agri_grant",
        "farm_asset", "commodity_supply", "food_innovation",
    ),
    "mining_and_natural_resources": (
        "mining", "mineral_exploration", "critical_minerals", "oil_gas",
        "water_resource", "forestry", "fisheries", "resource_licence",
        "resource_contract", "environmental_offset",
    ),
    "energy_and_utilities": (
        "electricity", "solar", "wind", "battery", "storage", "hydrogen",
        "grid", "utility_contract", "energy_efficiency", "energy_certificate",
        "energy_market", "waste_to_energy",
    ),
    "telecom_and_networks": (
        "telecommunications", "broadband", "fiber", "wireless", "satellite_comms",
        "network_services", "tower", "spectrum", "connectivity_program",
    ),
    "transport_and_mobility": (
        "freight", "shipping", "aviation", "rail", "public_transport",
        "fleet", "automotive", "ev", "charging", "mobility_service",
        "drone_service", "maritime",
    ),
    "hospitality_and_tourism": (
        "hotel", "hospitality", "tourism", "travel", "tour_operator",
        "events", "venue", "experience", "destination_program",
    ),
    "consumer_and_retail": (
        "consumer_product", "retail", "brand_partnership", "distribution",
        "franchise", "licensing", "private_label", "ecommerce",
        "subscription", "consumer_research",
    ),
    "gaming_and_interactive": (
        "game_development", "game_jam", "esports", "game_publishing",
        "game_asset", "modding", "interactive_media", "virtual_world",
    ),
    "arts_culture_and_heritage": (
        "arts_grant", "cultural_program", "museum", "heritage",
        "public_art", "creative_residency", "cultural_exchange",
    ),
    "sports_and_fitness": (
        "sports_contract", "athlete_partnership", "sponsorship_program",
        "sports_technology", "fitness_service", "sports_event",
    ),
    "standards_certification_and_compliance": (
        "standards", "certification", "accreditation", "compliance_program",
        "audit_program", "quality_program", "regulatory_submission",
    ),
    "intellectual_property_and_licensing": (
        "patent", "trademark", "copyright", "design_right", "technology_license",
        "patent_license", "royalty", "franchise_license", "know_how",
        "ip_acquisition",
    ),
    "legal_dispute_and_resolution": (
        "legal_contract", "legal_project", "due_diligence", "arbitration",
        "mediation", "claims", "dispute_resolution", "legal_research",
    ),
    "insurance_and_risk": (
        "insurance_contract", "reinsurance", "risk_program", "claims_services",
        "insurtech", "risk_data", "compliance_risk",
    ),
    "professional_expert_services": (
        "expert_network", "expert_witness", "due_diligence_service",
        "translation", "interpretation", "technical_writing", "copywriting",
        "design_service", "accounting", "tax_service", "audit_service",
        "recruiting", "staffing",
    ),
    "infrastructure_and_built_environment": (
        "civil_engineering", "architecture", "engineering_design",
        "project_management", "facilities_management", "property_management",
        "maintenance_contract", "infrastructure_finance", "infrastructure_ppp",
    ),
    "space_and_aerospace": (
        "space_launch", "satellite", "earth_observation", "space_data",
        "aerospace", "avionics", "space_grant", "space_research",
    ),
    "defence_and_public_safety": (
        "defence_procurement", "dual_use_technology", "public_safety",
        "emergency_management", "disaster_response", "resilience_program",
        "defence_research",
    ),
    "international_trade_and_development": (
        "export_opportunity", "import_opportunity", "trade_mission",
        "development_finance", "multilateral_grant", "international_procurement",
        "humanitarian_aid", "refugee_program", "capacity_building",
    ),
    "nonprofit_and_social_enterprise": (
        "nonprofit_contract", "social_enterprise", "impact_investment",
        "donor_program", "fundraising_service", "volunteer_program",
    ),
    "information_and_media_distribution": (
        "news", "newsletter", "podcast", "broadcast", "publishing",
        "journalism", "information_service", "media_rights", "syndication",
    ),
    "platform_and_marketplace_ecosystems": (
        "platform_listing", "marketplace_vendor", "app_store",
        "partner_directory", "affiliate_network", "referral_network",
        "creator_marketplace", "service_marketplace",
    ),
    "events_and_conferences": (
        "conference", "expo", "trade_show", "speaker", "sponsor",
        "exhibitor", "workshop", "meetup", "event_services",
    ),
    "other_and_emerging": (
        "unclassified", "new_market", "new_program", "new_mechanism",
        "second_order", "cross_domain", "unknown",
    ),
})

# Value mechanisms are independent of category: an opportunity may have more
# than one. This prevents the radar from becoming "money-only".
OPPORTUNITY_VALUE_MECHANISMS: Final[tuple[str, ...]] = (
    "cash_prize", "contract_revenue", "recurring_revenue", "investment",
    "grant", "tax_credit", "rebate", "royalty", "license_income",
    "equity", "token_reward", "bounty", "salary", "commission",
    "referral_fee", "affiliate_revenue", "sponsorship", "credits",
    "compute", "data_access", "distribution", "customer_access",
    "partnership", "ip_access", "credential", "publication",
    "reputation", "network_access", "other",
)

# What TitanOS may ultimately prepare/execute. Consequential actions still
# pass through the existing authorization gate.
OPPORTUNITY_ACTION_CLASSES: Final[tuple[str, ...]] = (
    "research", "analyze", "build", "repair", "test", "submit",
    "apply", "bid", "quote", "pitch", "propose", "contact",
    "negotiate", "contract", "invoice", "collect", "purchase",
    "sell", "license", "partner", "invest", "acquire", "publish",
    "contribute", "disclose", "audit", "register", "renew", "monitor",
)

OPPORTUNITY_ACCESS_MODELS: Final[tuple[str, ...]] = (
    "public", "open_application", "invite_only", "referral",
    "membership", "licensed", "accredited", "credentialed",
    "contractual", "permissioned", "authorized_security_scope",
    "geofenced", "jurisdiction_specific", "eligibility_restricted",
    "unknown",
)

OPPORTUNITY_COVERAGE_AXES: Final[tuple[str, ...]] = (
    "domain", "opportunity_type", "geography", "jurisdiction", "channel",
    "source", "language", "industry", "organization_size", "eligibility",
    "value_mechanism", "action_class", "access_model", "deadline_window",
    "freshness", "public_private", "new_secondary_signal", "second_order",
    "unknown_class",
)

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
