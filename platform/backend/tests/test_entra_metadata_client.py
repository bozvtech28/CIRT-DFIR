import pytest

from app.entra_metadata_client import (
    MetadataTrustError,
    fetch_trusted_document,
    validate_discovery_document,
    validate_jwks_document,
)


ISSUER = "https://login.microsoftonline.com/tenant-test/v2.0"
JWKS_URI = "https://login.microsoftonline.com/tenant-test/discovery/v2.0/keys"
HOSTS = {"login.microsoftonline.com"}


def valid_discovery():
    return {"issuer": ISSUER, "jwks_uri": JWKS_URI}


def valid_jwks():
    return {
        "keys": [
            {
                "kid": "synthetic-key-1",
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "n": "synthetic-modulus",
                "e": "AQAB",
            }
        ]
    }


def test_accepts_expected_discovery_document():
    metadata = validate_discovery_document(
        valid_discovery(),
        expected_issuer=ISSUER,
        allowed_jwks_hosts=HOSTS,
    )
    assert metadata.issuer == ISSUER
    assert metadata.jwks_uri == JWKS_URI


def test_rejects_wrong_issuer():
    document = valid_discovery()
    document["issuer"] = "https://attacker.example/issuer"
    with pytest.raises(MetadataTrustError):
        validate_discovery_document(
            document,
            expected_issuer=ISSUER,
            allowed_jwks_hosts=HOSTS,
        )


def test_rejects_http_jwks_url():
    document = valid_discovery()
    document["jwks_uri"] = "http://login.microsoftonline.com/keys"
    with pytest.raises(MetadataTrustError):
        validate_discovery_document(
            document,
            expected_issuer=ISSUER,
            allowed_jwks_hosts=HOSTS,
        )


def test_rejects_unapproved_jwks_host():
    document = valid_discovery()
    document["jwks_uri"] = "https://attacker.example/keys"
    with pytest.raises(MetadataTrustError):
        validate_discovery_document(
            document,
            expected_issuer=ISSUER,
            allowed_jwks_hosts=HOSTS,
        )


def test_rejects_missing_expected_issuer():
    with pytest.raises(MetadataTrustError):
        validate_discovery_document(
            valid_discovery(),
            expected_issuer="",
            allowed_jwks_hosts=HOSTS,
        )


def test_transport_is_injected_and_receives_timeout():
    calls = []

    def fake_transport(url, timeout):
        calls.append((url, timeout))
        return valid_discovery()

    result = fetch_trusted_document(
        "https://login.microsoftonline.com/discovery",
        trusted_hosts=HOSTS,
        transport=fake_transport,
        timeout_seconds=2.0,
    )

    assert result["issuer"] == ISSUER
    assert calls == [
        ("https://login.microsoftonline.com/discovery", 2.0)
    ]


def test_rejects_unapproved_fetch_host_before_transport():
    calls = []

    def fake_transport(url, timeout):
        calls.append(url)
        return {}

    with pytest.raises(MetadataTrustError):
        fetch_trusted_document(
            "https://attacker.example/discovery",
            trusted_hosts=HOSTS,
            transport=fake_transport,
        )

    assert calls == []


def test_rejects_non_https_fetch_url():
    with pytest.raises(MetadataTrustError):
        fetch_trusted_document(
            "http://login.microsoftonline.com/discovery",
            trusted_hosts=HOSTS,
            transport=lambda url, timeout: {},
        )


def test_rejects_timeout_outside_bound():
    with pytest.raises(MetadataTrustError):
        fetch_trusted_document(
            "https://login.microsoftonline.com/discovery",
            trusted_hosts=HOSTS,
            transport=lambda url, timeout: {},
            timeout_seconds=30,
        )


def test_rejects_non_object_transport_response():
    with pytest.raises(MetadataTrustError):
        fetch_trusted_document(
            "https://login.microsoftonline.com/discovery",
            trusted_hosts=HOSTS,
            transport=lambda url, timeout: [],
        )


def test_accepts_structurally_valid_jwks():
    result = validate_jwks_document(valid_jwks())
    assert result["keys"][0]["kid"] == "synthetic-key-1"


@pytest.mark.parametrize("document", [None, [], {}, {"keys": []}])
def test_rejects_invalid_jwks_container(document):
    with pytest.raises(MetadataTrustError):
        validate_jwks_document(document)


def test_rejects_duplicate_key_ids():
    document = valid_jwks()
    document["keys"].append(dict(document["keys"][0]))
    with pytest.raises(MetadataTrustError):
        validate_jwks_document(document)


def test_rejects_non_rsa_key():
    document = valid_jwks()
    document["keys"][0]["kty"] = "EC"
    with pytest.raises(MetadataTrustError):
        validate_jwks_document(document)


def test_rejects_private_key_material():
    document = valid_jwks()
    document["keys"][0]["d"] = "synthetic-private-value"
    with pytest.raises(MetadataTrustError):
        validate_jwks_document(document)


def test_rejects_wrong_algorithm():
    document = valid_jwks()
    document["keys"][0]["alg"] = "HS256"
    with pytest.raises(MetadataTrustError):
        validate_jwks_document(document)


def test_rejects_encryption_key():
    document = valid_jwks()
    document["keys"][0]["use"] = "enc"
    with pytest.raises(MetadataTrustError):
        validate_jwks_document(document)


def test_rejects_missing_key_id():
    document = valid_jwks()
    document["keys"][0].pop("kid")
    with pytest.raises(MetadataTrustError):
        validate_jwks_document(document)