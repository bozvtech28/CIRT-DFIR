import pytest

from synthetic_test_support.synthetic_role_mapping import (
    map_synthetic_roles_to_permissions,
)


def test_viewer_gets_read_only_permission():
    assert map_synthetic_roles_to_permissions(["Viewer"]) == frozenset({
        "cases:read",
    })


def test_analyst_gets_read_and_update_permissions():
    assert map_synthetic_roles_to_permissions(["Analyst"]) == frozenset({
        "cases:read",
        "cases:update",
    })


def test_admin_gets_proposed_admin_permissions():
    assert map_synthetic_roles_to_permissions(["Admin"]) == frozenset({
        "cases:read",
        "cases:update",
        "users:manage",
        "audit:read",
    })


def test_multiple_known_roles_union_permissions():
    assert map_synthetic_roles_to_permissions(["Viewer", "Analyst"]) == frozenset({
        "cases:read",
        "cases:update",
    })


def test_unknown_role_fails_closed():
    with pytest.raises(ValueError, match="Unknown synthetic role"):
        map_synthetic_roles_to_permissions(["Viewer", "SuperUser"])


def test_empty_roles_fail_closed():
    with pytest.raises(ValueError):
        map_synthetic_roles_to_permissions([])


@pytest.mark.parametrize("roles", [
    "Admin",
    b"Admin",
    [""],
    ["   "],
    [None],
    [123],
    None,
])
def test_malformed_role_input_fails_closed(roles):
    with pytest.raises(ValueError):
        map_synthetic_roles_to_permissions(roles)


def test_role_matching_is_case_sensitive():
    with pytest.raises(ValueError, match="Unknown synthetic role"):
        map_synthetic_roles_to_permissions(["admin"])


def test_duplicate_roles_do_not_escalate_permissions():
    assert map_synthetic_roles_to_permissions(["Viewer", "Viewer"]) == frozenset({
        "cases:read",
    })


def test_no_browser_or_identity_claims_are_accepted_as_permissions():
    with pytest.raises(ValueError, match="Unknown synthetic role"):
        map_synthetic_roles_to_permissions(["cases:update"])


def test_returned_permissions_cannot_be_mutated():
    result = map_synthetic_roles_to_permissions(["Viewer"])
    assert isinstance(result, frozenset)
    with pytest.raises(AttributeError):
        result.add("users:manage")
