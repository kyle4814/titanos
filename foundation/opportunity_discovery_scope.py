"""Global opportunity discovery coverage registry.

This layer maps the taxonomy to *where* opportunities can be observed.
It is intentionally source-agnostic: concrete URLs, credentials and parsers
belong in source adapters. Unknown/unclassified surfaces remain first-class.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from foundation.opportunity_scope import OPPORTUNITY_DOMAINS, OPPORTUNITY_GEOGRAPHIES


@dataclass(frozen=True)
class DiscoverySurface:
    id: str
    class_name: str
    geography: str
    domains: tuple[str, ...]
    access: str
    cadence_hint: str
    notes: str = ""


# Registry classes rather than an invented list of websites. Adapters can
# populate concrete sources beneath each class without changing the contract.
DISCOVERY_SURFACE_CLASSES: Final[tuple[str, ...]] = (
    "FEDERAL_GOVERNMENT",
    "STATE_REGIONAL_GOVERNMENT",
    "LOCAL_GOVERNMENT",
    "PUBLIC_PROCUREMENT",
    "PUBLIC_GRANTS",
    "PUBLIC_RESEARCH",
    "REGULATOR",
    "PUBLIC_REGISTRY",
    "SECURITY_PROGRAM_REGISTRY",
    "BUG_BOUNTY_PLATFORM",
    "OPEN_SOURCE_HOSTING",
    "PACKAGE_REGISTRY",
    "RESEARCH_REPOSITORY",
    "DATA_PORTAL",
    "CHALLENGE_PLATFORM",
    "INVESTOR_DATABASE",
    "FUND_MANAGER",
    "ACCELERATOR_NETWORK",
    "JOB_MARKETPLACE",
    "FREELANCE_MARKETPLACE",
    "SERVICE_MARKETPLACE",
    "BUSINESS_MARKETPLACE",
    "DOMAIN_ASSET_MARKETPLACE",
    "SAAS_MARKETPLACE",
    "APP_PLUGIN_MARKETPLACE",
    "DEVELOPER_ECOSYSTEM",
    "API_DIRECTORY",
    "PARTNER_DIRECTORY",
    "AFFILIATE_NETWORK",
    "ECOSYSTEM_GOVERNANCE",
    "BLOCKCHAIN_DATA",
    "NEWS_AND_PRESS",
    "COMPANY_SIGNAL",
    "PROFESSIONAL_NETWORK",
    "COMMUNITY_FORUM",
    "EVENT_PLATFORM",
    "TRADE_ASSOCIATION",
    "STANDARDS_BODY",
    "ACADEMIC_INSTITUTION",
    "FOUNDATION_PHILANTHROPY",
    "NONPROFIT_PROCUREMENT",
    "INTERNATIONAL_ORGANIZATION",
    "TRADE_MISSION",
    "PHYSICAL_ASSET_MARKET",
    "OTHER_WEB",
    "DIRECT_SUBMISSION",
    "REFERRAL",
)

# Jurisdiction is an adapter dimension. These are coverage tiers, not a claim
# that TitanOS currently has adapters for every country or agency.
JURISDICTION_TIERS: Final[tuple[str, ...]] = (
    "MULTILATERAL",
    "CONTINENTAL_UNION",
    "NATIONAL",
    "STATE_PROVINCE",
    "TERRITORY",
    "COUNTY_DISTRICT",
    "MUNICIPAL",
    "INDIGENOUS_GOVERNANCE",
    "REGULATORY",
    "PRIVATE",
    "CROSS_BORDER",
)

GLOBAL_REGION_GROUPS: Final[tuple[str, ...]] = (
    "AFRICA", "ASIA", "EUROPE", "NORTH_AMERICA", "SOUTH_AMERICA",
    "OCEANIA", "MIDDLE_EAST", "CENTRAL_AMERICA", "CARIBBEAN",
    "POLAR_AND_OCEAN", "GLOBAL",
)

# High-level source families. Concrete adapters should record provenance,
# retrieval time, parser version and terms/authorization.
SOURCE_FAMILIES: Final[dict[str, tuple[str, ...]]] = {
    "PUBLIC": (
        "government", "procurement", "grants", "regulator", "public_registry",
        "public_research", "public_data", "public_assets",
    ),
    "TECHNICAL": (
        "github", "gitlab", "package_registry", "bug_bounty", "vdp",
        "cve", "api_directory", "developer_program", "cloud_program",
        "open_source_foundation",
    ),
    "CAPITAL": (
        "investor", "fund", "accelerator", "incubator", "crowdfunding",
        "family_office", "private_equity", "debt",
    ),
    "COMMERCIAL": (
        "company", "marketplace", "vendor", "supplier", "partner",
        "reseller", "affiliate", "job", "freelance", "services",
    ),
    "RESEARCH": (
        "academic", "research_repository", "challenge", "dataset",
        "scientific_program", "fellowship",
    ),
    "WEB3": (
        "protocol", "chain", "dao", "ecosystem", "web3_grant",
        "web3_bounty", "web3_hackathon",
    ),
    "MEDIA_SIGNAL": (
        "news", "press_release", "professional_network", "community",
        "social_signal", "event",
    ),
    "ASSET": (
        "domain", "website", "saas", "ip", "property", "equipment",
        "business", "industrial_asset",
    ),
    "INTERNATIONAL": (
        "multilateral", "development", "humanitarian", "trade",
        "international_procurement",
    ),
    "DIRECT": (
        "direct_request", "referral", "email", "submission",
    ),
}


def coverage_matrix() -> dict[str, tuple[str, ...]]:
    """Return the declared global coverage dimensions for radar planning."""
    return {
        "regions": GLOBAL_REGION_GROUPS,
        "jurisdiction_tiers": JURISDICTION_TIERS,
        "surface_classes": DISCOVERY_SURFACE_CLASSES,
        "source_families": tuple(SOURCE_FAMILIES),
        "domain_keys": tuple(sorted(OPPORTUNITY_DOMAINS)),
        "geography_tiers": OPPORTUNITY_GEOGRAPHIES,
    }
