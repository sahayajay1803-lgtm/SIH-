from app.schemas import BusinessProfileCreate, ProjectStage
from app.services.rules import evaluate_profile


def test_rules_are_deterministic_and_include_dependencies():
    profile = BusinessProfileCreate(name="Priya Foods", industry_category="food_processing", location_district="Pune", investment_amount=6_000_000, project_stage=ProjectStage.new_setup, employee_count=18)
    first = evaluate_profile(profile)
    second = evaluate_profile(profile)
    assert first == second
    assert {approval.approval_id for approval in first} == {"factory_license", "pollution_consent", "local_body_noc", "fire_noc"}
    assert second[-1].dependencies == ["local_body_noc"]
