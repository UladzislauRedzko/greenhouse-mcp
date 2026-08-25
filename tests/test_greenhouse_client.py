import httpx
import pytest

from src.greenhouse_client import GreenhouseClient


class CapturingClient(GreenhouseClient):
    def __init__(self):
        super().__init__(access_token="test-token")
        self.captured_endpoint = None
        self.captured_params = None
        self.captured_page = None

    async def _get_paginated_page(self, endpoint, params, page):
        self.captured_endpoint = endpoint
        self.captured_params = params
        self.captured_page = page
        return []


@pytest.mark.asyncio
async def test_static_access_token_uses_bearer_header():
    client = GreenhouseClient(access_token="test-token")

    headers = await client._headers()

    assert headers["Authorization"] == "Bearer test-token"


def test_extract_next_url_from_link_header():
    client = GreenhouseClient(access_token="test-token")
    response = httpx.Response(
        200,
        headers={
            "Link": '<https://harvest.greenhouse.io/v3/jobs?cursor=abc>; rel="next"'
        },
    )

    assert (
        client._extract_next_url(response)
        == "https://harvest.greenhouse.io/v3/jobs?cursor=abc"
    )


@pytest.mark.asyncio
async def test_list_applications_uses_v3_filter_names():
    client = CapturingClient()

    await client.list_applications(
        per_page=50,
        page=2,
        job_id=123,
        candidate_id=456,
        status="active",
        created_after="2026-01-01T00:00:00Z",
        created_before="2026-01-31T23:59:59Z",
    )

    assert client.captured_endpoint == "applications"
    assert client.captured_page == 2
    assert client.captured_params == {
        "per_page": 50,
        "created_at[gte]": "2026-01-01T00:00:00Z",
        "created_at[lte]": "2026-01-31T23:59:59Z",
        "job_ids": "123",
        "candidate_ids": "456",
        "status": "active",
    }


@pytest.mark.asyncio
async def test_list_candidates_uses_ids_filter():
    client = CapturingClient()

    await client.list_candidates(candidate_ids=[1, 2, 3], email="person@example.com")

    assert client.captured_endpoint == "candidates"
    assert client.captured_params["ids"] == "1,2,3"
    assert client.captured_params["email"] == "person@example.com"
