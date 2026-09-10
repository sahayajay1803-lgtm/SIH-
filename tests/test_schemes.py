from app.services.schemes import list_schemes


def test_scheme_catalogue_contains_central_and_state_programmes():
    schemes = list_schemes()
    assert {scheme.government_level for scheme in schemes} == {"central", "state"}


def test_scheme_catalogue_filters_by_search_and_level():
    schemes = list_schemes(search="food", government_level="central")
    assert len(schemes) == 1
    assert schemes[0].scheme_id == "pmfme"