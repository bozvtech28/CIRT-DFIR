import json
from functools import partial

import httpx
import pytest

from app.entra_http_transport import fetch_json_document
from app.entra_metadata_client import MetadataTrustError


URL = "https://login.microsoftonline.com/discovery/v2.0/keys"
HOSTS = {"login.microsoftonline.com"}


def make_client_factory(handler):
    return partial(httpx.Client, transport=httpx.MockTransport(handler))


def json_response(document, status_code=200, headers=None):
    response_headers = {"content-type": "application/json"}
    if headers:
        response_headers.update(headers)
    return httpx.Response(
        status_code,
        headers=response_headers,
        content=json.dumps(document).encode("utf-8"),
    )


def test_accepts_trusted_json_object_without_network():
    calls = []

    def handler(request):
        calls.append(request)
        return json_response({"keys": []})

    result = fetch_json_document(
        URL,
        trusted_hosts=HOSTS,
        client_factory=make_client_factory(handler),
    )

    assert result == {"keys": []}
    assert len(calls) == 1
    assert calls[0].url.scheme == "https"
    assert calls[0].headers["accept"] == "application/json"


@pytest.mark.parametrize(
    "url",
    [
        "http://login.microsoftonline.com/keys",
        "https://attacker.example/keys",
        "https://user:pass@login.microsoftonline.com/keys",
        "https://login.microsoftonline.com/keys#fragment",
    ],
)
def test_rejects_untrusted_or_unsafe_url_before_request(url):
    calls = []

    def handler(request):
        calls.append(request)
        return json_response({})

    with pytest.raises(MetadataTrustError):
        fetch_json_document(
            url,
            trusted_hosts=HOSTS,
            client_factory=make_client_factory(handler),
        )

    assert calls == []


def test_rejects_redirect_without_following_it():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            302,
            headers={"location": "https://attacker.example/"},
        )

    with pytest.raises(MetadataTrustError, match="status"):
        fetch_json_document(
            URL,
            trusted_hosts=HOSTS,
            client_factory=make_client_factory(handler),
        )

    assert len(calls) == 1


def test_rejects_non_success_status():
    def handler(request):
        return httpx.Response(503)

    with pytest.raises(MetadataTrustError, match="status"):
        fetch_json_document(
            URL,
            trusted_hosts=HOSTS,
            client_factory=make_client_factory(handler),
        )


def test_rejects_non_json_content_type():
    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/plain"}, content=b"{}")

    with pytest.raises(MetadataTrustError, match="JSON content"):
        fetch_json_document(
            URL,
            trusted_hosts=HOSTS,
            client_factory=make_client_factory(handler),
        )


def test_rejects_declared_oversized_body():
    def handler(request):
        return httpx.Response(
            200,
            headers={
                "content-type": "application/json",
                "content-length": "1000",
            },
            content=b"{}",
        )

    with pytest.raises(MetadataTrustError, match="size limit"):
        fetch_json_document(
            URL,
            trusted_hosts=HOSTS,
            max_response_bytes=100,
            client_factory=make_client_factory(handler),
        )


def test_rejects_streamed_oversized_body():
    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'{"data":"' + (b"x" * 200) + b'"}',
        )

    with pytest.raises(MetadataTrustError, match="size limit"):
        fetch_json_document(
            URL,
            trusted_hosts=HOSTS,
            max_response_bytes=100,
            client_factory=make_client_factory(handler),
        )


@pytest.mark.parametrize("body", [b"{", b"[]", b"null", b'"text"'])
def test_rejects_invalid_json_or_non_object(body):
    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=body,
        )

    with pytest.raises(MetadataTrustError):
        fetch_json_document(
            URL,
            trusted_hosts=HOSTS,
            client_factory=make_client_factory(handler),
        )


@pytest.mark.parametrize("timeout", [0, -1, 11, True, "3"])
def test_rejects_invalid_timeout(timeout):
    with pytest.raises(MetadataTrustError):
        fetch_json_document(URL, trusted_hosts=HOSTS, timeout_seconds=timeout)


@pytest.mark.parametrize("limit", [0, -1, 4 * 1024 * 1024 + 1, True, "100"])
def test_rejects_invalid_response_size_limit(limit):
    with pytest.raises(MetadataTrustError):
        fetch_json_document(URL, trusted_hosts=HOSTS, max_response_bytes=limit)


def test_rejects_empty_allowlist_before_request():
    calls = []

    def handler(request):
        calls.append(request)
        return json_response({})

    with pytest.raises(MetadataTrustError, match="allowlist"):
        fetch_json_document(
            URL,
            trusted_hosts=set(),
            client_factory=make_client_factory(handler),
        )

    assert calls == []


def test_accepts_json_with_parameters_in_content_type():
    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "application/json; charset=utf-8"},
            content=b'{"issuer":"synthetic"}',
        )

    assert fetch_json_document(
        URL,
        trusted_hosts=HOSTS,
        client_factory=make_client_factory(handler),
    ) == {"issuer": "synthetic"}


@pytest.mark.parametrize(
    "url",
    [
        "https://login.microsoftonline.com:8443/discovery",
        "https://login.microsoftonline.com:80/discovery",
    ],
)
def test_rejects_nonstandard_https_ports_before_request(url):
    calls = []

    def handler(request):
        calls.append(request)
        return json_response({})

    with pytest.raises(MetadataTrustError, match="port 443"):
        fetch_json_document(
            url,
            trusted_hosts=HOSTS,
            client_factory=make_client_factory(handler),
        )

    assert calls == []


def test_accepts_explicit_standard_https_port():
    def handler(request):
        assert request.url.port == 443
        return json_response({"issuer": "synthetic"})

    result = fetch_json_document(
        "https://login.microsoftonline.com:443/discovery",
        trusted_hosts=HOSTS,
        client_factory=make_client_factory(handler),
    )

    assert result == {"issuer": "synthetic"}
