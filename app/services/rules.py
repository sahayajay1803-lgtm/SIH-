from app.schemas import Approval, BusinessProfileCreate


# Illustrative seed data only. Replace with legally verified Maharashtra rules.
APPROVAL_RULES = [
    {
        "approval_id": "factory_license",
        "name": "Factory License",
        "department": "Directorate of Industrial Safety and Health",
        "required_documents": ["site_plan", "occupier_identity", "process_description"],
        "sla_days": 30,
        "dependencies": [],
        "source": "Illustrative placeholder - verify with the competent authority",
        "when": lambda p: p.industry_category.lower() in {"manufacturing", "food_processing"},
        "reason": "Your profile describes a manufacturing activity, so a factory license is included for the demo.",
    },
    {
        "approval_id": "pollution_consent",
        "name": "Consent to Establish",
        "department": "Maharashtra Pollution Control Board",
        "required_documents": ["site_plan", "process_description", "water_balance"],
        "sla_days": 45,
        "dependencies": [],
        "source": "Illustrative placeholder - verify with the competent authority",
        "when": lambda p: p.industry_category.lower() in {"manufacturing", "food_processing", "chemical"},
        "reason": "The selected industrial category may create environmental impacts and is included in the demo rule set.",
    },
    {
        "approval_id": "local_body_noc",
        "name": "Local Body No-Objection Certificate",
        "department": "Local Municipal Authority",
        "required_documents": ["lease_or_ownership_proof", "layout_plan"],
        "sla_days": 21,
        "dependencies": [],
        "source": "Illustrative placeholder - verify with the competent authority",
        "when": lambda p: p.project_stage.value == "new_setup",
        "reason": "A new setup needs a local-site clearance in this illustrative workflow.",
    },
    {
        "approval_id": "fire_noc",
        "name": "Fire Safety No-Objection Certificate",
        "department": "Local Fire Department",
        "required_documents": ["building_plan", "fire_system_plan"],
        "sla_days": 30,
        "dependencies": ["local_body_noc"],
        "source": "Illustrative placeholder - verify with the competent authority",
        "when": lambda p: p.employee_count >= 10 or p.investment_amount >= 5_000_000,
        "reason": "The employee or investment scale crosses the illustrative fire-safety trigger.",
    },
]


def evaluate_profile(profile: BusinessProfileCreate) -> list[Approval]:
    return [
        Approval(
            approval_id=rule["approval_id"],
            name=rule["name"],
            department=rule["department"],
            required_documents=rule["required_documents"],
            sla_days=rule["sla_days"],
            dependencies=rule["dependencies"],
            source=rule["source"],
            applicability_reason=rule["reason"],
        )
        for rule in APPROVAL_RULES
        if rule["when"](profile)
    ]


def find_approval(approval_id: str) -> Approval | None:
    for rule in APPROVAL_RULES:
        if rule["approval_id"] == approval_id:
            return Approval(
                approval_id=rule["approval_id"], name=rule["name"], department=rule["department"],
                required_documents=rule["required_documents"], sla_days=rule["sla_days"],
                dependencies=rule["dependencies"], source=rule["source"], applicability_reason=rule["reason"],
            )
    return None
