from datetime import date

from app.schemas import BusinessProfileCreate, Scheme, SchemeMatch


SCHEMES = [
    Scheme(
        scheme_id="pmfme",
        name="PM Formalisation of Micro Food Processing Enterprises",
        government_level="central",
        department="Ministry of Food Processing Industries",
        category="food_processing",
        description="Credit-linked capital subsidy and support for formalising micro food-processing enterprises.",
        benefits=["Credit-linked subsidy", "Training and handholding", "Branding and marketing support"],
        eligibility=["Micro food-processing enterprise", "Existing or proposed food-processing activity", "Applicant contribution and bank finance subject to scheme rules"],
        required_documents=["Identity proof", "Business constitution proof", "Project report", "Bank details"],
        application_url="https://pmfme.mofpi.gov.in/",
        source_url="https://pmfme.mofpi.gov.in/",
        last_verified_at=date(2026, 9, 1),
        tags=["food", "msme", "subsidy"],
    ),
    Scheme(
        scheme_id="cmegp_maharashtra",
        name="Chief Minister Employment Generation Programme",
        government_level="state",
        department="Government of Maharashtra - Industries Department",
        category="entrepreneurship",
        description="State support for eligible new micro and small enterprises creating local employment.",
        benefits=["Margin money subsidy", "Entrepreneurship support", "Employment-linked assistance"],
        eligibility=["New micro or small enterprise", "Maharashtra residence or project connection", "Applicant contribution and financing requirements"],
        required_documents=["Aadhaar or identity proof", "Residence proof", "Project report", "Category certificate if applicable"],
        application_url="https://www.mahaonline.gov.in/",
        source_url="https://industry.maharashtra.gov.in/",
        last_verified_at=date(2026, 9, 1),
        tags=["maharashtra", "employment", "msme"],
    ),
    Scheme(
        scheme_id="msme_technology_upgrade",
        name="MSME Technology Upgradation Support",
        government_level="central",
        department="Ministry of Micro, Small and Medium Enterprises",
        category="technology",
        description="Illustrative technology-upgradation support for eligible MSMEs adopting productivity or quality improvements.",
        benefits=["Technology adoption support", "Quality certification assistance", "Productivity improvement"],
        eligibility=["Udyam-registered MSME", "Eligible technology or quality-improvement project", "Verified investment proposal"],
        required_documents=["Udyam registration", "Vendor quotation", "Project report", "Financial statements"],
        application_url="https://www.udyamregistration.gov.in/",
        source_url="https://msme.gov.in/",
        last_verified_at=date(2026, 9, 1),
        tags=["msme", "technology", "quality"],
    ),
    Scheme(
        scheme_id="maharashtra_startup_policy",
        name="Maharashtra Startup and Innovation Support",
        government_level="state",
        department="Maharashtra State Innovation Society",
        category="innovation",
        description="Illustrative state support for recognised startups building innovative products or services in Maharashtra.",
        benefits=["Incubation access", "Mentoring", "Innovation challenge opportunities"],
        eligibility=["Innovation-led startup", "Maharashtra operations or registration", "Application accepted through the relevant programme window"],
        required_documents=["Incorporation certificate", "Pitch deck", "Founder identity proof", "Product or prototype note"],
        application_url="https://msins.in/",
        source_url="https://msins.in/",
        last_verified_at=date(2026, 9, 1),
        tags=["startup", "innovation", "maharashtra"],
    ),
]


def list_schemes(search: str = "", government_level: str | None = None, category: str | None = None) -> list[Scheme]:
    query = search.strip().lower()
    return [
        scheme for scheme in SCHEMES
        if (not query or query in f"{scheme.name} {scheme.description} {' '.join(scheme.tags)}".lower())
        and (not government_level or scheme.government_level == government_level)
        and (not category or scheme.category == category)
    ]


def match_schemes(profile: BusinessProfileCreate) -> list[SchemeMatch]:
    industry = profile.industry_category.lower()
    matches: list[SchemeMatch] = []
    for scheme in SCHEMES:
        score = 35
        reasons = ["The scheme is included in the current illustrative catalogue."]
        if scheme.category == "food_processing" and "food" in industry:
            score += 45
            reasons.append("The profile industry matches food processing.")
        if scheme.category == "entrepreneurship" and profile.project_stage.value == "new_setup":
            score += 35
            reasons.append("The profile describes a new setup.")
        if scheme.category == "technology" and profile.project_stage.value in {"expansion", "operating"}:
            score += 25
            reasons.append("The project stage may suit technology improvement support.")
        if scheme.category == "innovation" and any(word in industry for word in ("technology", "software", "innovation")):
            score += 40
            reasons.append("The industry description suggests an innovation-led activity.")
        matches.append(SchemeMatch(scheme=scheme, match_score=min(score, 100), reasons=reasons))
    return sorted(matches, key=lambda item: item.match_score, reverse=True)