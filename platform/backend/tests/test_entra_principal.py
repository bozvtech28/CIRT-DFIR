import pytest

from app.security import KNOWN_ROLES
from app.entra_principal import (
    PrincipalMappingError,
    principal_from_verified_claims,
)


TEST_ROLE_MAP = {
    "CIRT.DFIR.Viewer": "Viewer",
    "CIRT.DFIR.Analyst": "DFIR Analyst",
    "CIRT.DFIR.Administrator": "Administrator",
}


def test_maps_verified_analyst_role():
    principal = principal_from_verified_claims(
        {"sub": "synthetic-user-01", "roles": ["CIRT.DFIR.Analyst"]},
        approved_role_map=TEST_ROLE_MAP,
    )
    assert principal.subject == "synthetic-user-01"
    assert principal.roles == frozenset({"DFIR Analyst"})


def test_maps_multiple_approved_roles():
    principal = principal_from_verified_claims(
        {
            "sub": "synthetic-user-02",
            "roles": ["CIRT.DFIR.Viewer", "CIRT.DFIR.Analyst"],
        },
        approved_role_map=TEST_ROLE_MAP,
    )
    assert principal.roles == frozenset({"Viewer", "DFIR Analyst"})


def test_subject_is_trimmed():
    principal = principal_from_verified_claims(
        {"sub": "  synthetic-user-03  ", "roles": ["CIRT.DFIR.Viewer"]},
        approved_role_map=TEST_ROLE_MAP,
    )
    assert principal.subject == "synthetic-user-03"


@pytest.mark.parametrize("claims", [
    None,
    [],
    "not-a-claims-object",
])
def test_rejects_non_mapping_claims(claims):
    with pytest.raises(PrincipalMappingError):
        principal_from_verified_claims(
            claims,
            approved_role_map=TEST_ROLE_MAP,
        )


@pytest.mark.parametrize("claims", [
    {"roles": ["CIRT.DFIR.Analyst"]},
    {"sub": "", "roles": ["CIRT.DFIR.Analyst"]},
    {"sub": "   ", "roles": ["CIRT.DFIR.Analyst"]},
    {"sub": 123, "roles": ["CIRT.DFIR.Analyst"]},
])
def test_rejects_missing_or_invalid_subject(claims):
    with pytest.raises(PrincipalMappingError):
        principal_from_verified_claims(
            claims,
            approved_role_map=TEST_ROLE_MAP,
        )


@pytest.mark.parametrize("claims", [
    {"sub": "synthetic-user", "roles": "CIRT.DFIR.Analyst"},
    {"sub": "synthetic-user", "roles": []},
    {"sub": "synthetic-user"},
    {"sub": "synthetic-user", "roles": [None]},
    {"sub": "synthetic-user", "roles": [""]},
    {
        "sub": "synthetic-user",
        "roles": ["CIRT.DFIR.Analyst", "CIRT.DFIR.Analyst"],
    },
])
def test_rejects_missing_malformed_or_duplicate_roles(claims):
    with pytest.raises(PrincipalMappingError):
        principal_from_verified_claims(
            claims,
            approved_role_map=TEST_ROLE_MAP,
        )


def test_rejects_unapproved_application_role():
    with pytest.raises(PrincipalMappingError):
        principal_from_verified_claims(
            {"sub": "synthetic-user", "roles": ["CIRT.DFIR.SuperUser"]},
            approved_role_map=TEST_ROLE_MAP,
        )


@pytest.mark.parametrize("role_map", [
    {},
    None,
    {"CIRT.DFIR.Analyst": "SuperUser"},
    {"": "Viewer"},
    {"CIRT.DFIR.Analyst": ""},
])
def test_rejects_missing_or_invalid_server_role_map(role_map):
    with pytest.raises(PrincipalMappingError):
        principal_from_verified_claims(
            {"sub": "synthetic-user", "roles": ["CIRT.DFIR.Analyst"]},
            approved_role_map=role_map,
        )


def test_internal_role_values_are_known():
    assert set(TEST_ROLE_MAP.values()).issubset(KNOWN_ROLES)


def test_ignores_unrelated_claims_and_does_not_grant_from_groups():
    principal = principal_from_verified_claims(
        {
            "sub": "synthetic-user",
            "groups": ["CIRT.DFIR.Administrator"],
            "scp": "cases:update",
            "roles": ["CIRT.DFIR.Viewer"],
        },
        approved_role_map=TEST_ROLE_MAP,
    )
    assert principal.roles == frozenset({"Viewer"})
