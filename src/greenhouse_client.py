import asyncio
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv

load_dotenv()


class GreenhouseClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("GREENHOUSE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GREENHOUSE_CLIENT_SECRET")
        self.user_id = user_id or os.getenv("GREENHOUSE_USER_ID")
        self.access_token = access_token or os.getenv("GREENHOUSE_ACCESS_TOKEN")

        if not self.access_token and not (self.client_id and self.client_secret):
            raise ValueError(
                "Greenhouse Harvest v3 credentials are required. Set "
                "GREENHOUSE_CLIENT_ID and GREENHOUSE_CLIENT_SECRET, or "
                "GREENHOUSE_ACCESS_TOKEN for local testing."
            )

        self.base_url = os.getenv(
            "GREENHOUSE_BASE_URL", "https://harvest.greenhouse.io/v3"
        )
        self.auth_url = os.getenv(
            "GREENHOUSE_AUTH_URL", "https://auth.greenhouse.io/token"
        )

        self._token_expires_at = 0.0
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window = 10
        self._rate_limit_max = 50

    async def _rate_limit(self):
        current_time = time.time()
        if current_time - self._last_request_time > self._rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time

        if self._request_count >= self._rate_limit_max:
            sleep_time = self._rate_limit_window - (
                current_time - self._last_request_time
            )
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()

        self._request_count += 1

    async def _fetch_access_token(self) -> str:
        data = {"grant_type": "client_credentials"}
        if self.user_id:
            data["sub"] = str(self.user_id)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.auth_url,
                auth=httpx.BasicAuth(self.client_id, self.client_secret),
                data=data,
                timeout=30.0,
            )
            response.raise_for_status()
            token_data = response.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Greenhouse token response did not include access_token")

        self.access_token = access_token
        expires_in = int(token_data.get("expires_in", 300))
        self._token_expires_at = time.time() + max(expires_in - 60, 0)
        return access_token

    async def _get_access_token(self) -> str:
        if self.access_token and self._token_expires_at == 0:
            return self.access_token

        if self.access_token and time.time() < self._token_expires_at:
            return self.access_token

        return await self._fetch_access_token()

    async def _headers(self) -> Dict[str, str]:
        token = await self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _url_for(self, endpoint_or_url: str) -> str:
        if endpoint_or_url.startswith("http://") or endpoint_or_url.startswith(
            "https://"
        ):
            return endpoint_or_url
        return urljoin(f"{self.base_url.rstrip('/')}/", endpoint_or_url.lstrip("/"))

    def _extract_next_url(self, response: httpx.Response) -> Optional[str]:
        link_header = response.headers.get("Link")
        if not link_header:
            return None

        for link in link_header.split(","):
            parts = link.split(";")
            if len(parts) < 2:
                continue

            url_part = parts[0].strip()
            rel_parts = [part.strip() for part in parts[1:]]
            if 'rel="next"' not in rel_parts and "rel=next" not in rel_parts:
                continue

            if url_part.startswith("<") and url_part.endswith(">"):
                return url_part[1:-1]

        return None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_on_unauthorized: bool = True,
    ) -> Any:
        response = await self._make_response(
            method=method,
            endpoint=endpoint,
            params=params,
            json_data=json_data,
            retry_on_unauthorized=retry_on_unauthorized,
        )

        if response.status_code == 204 or not response.content:
            return {}

        return response.json()

    async def _make_response(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_on_unauthorized: bool = True,
    ) -> httpx.Response:
        await self._rate_limit()

        url = self._url_for(endpoint)

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=await self._headers(),
                params=params,
                json=json_data,
                timeout=30.0,
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                await asyncio.sleep(retry_after)
                return await self._make_response(
                    method,
                    endpoint,
                    params,
                    json_data,
                    retry_on_unauthorized=retry_on_unauthorized,
                )

            if response.status_code == 401 and retry_on_unauthorized and self.client_id:
                self.access_token = None
                self._token_expires_at = 0.0
                return await self._make_response(
                    method,
                    endpoint,
                    params,
                    json_data,
                    retry_on_unauthorized=False,
                )

            response.raise_for_status()

            return response

    def _add_date_filters(
        self,
        params: Dict[str, Any],
        field_name: str,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> None:
        if after:
            params[f"{field_name}[gte]"] = after
        if before:
            params[f"{field_name}[lte]"] = before

    def _ids_param(self, ids: Optional[List[int]]) -> Optional[str]:
        if not ids:
            return None
        return ",".join(map(str, ids))

    async def _get_paginated_page(
        self,
        endpoint: str,
        params: Dict[str, Any],
        page: int,
    ) -> List[Dict[str, Any]]:
        if page < 1:
            raise ValueError("page must be greater than or equal to 1")

        response = await self._make_response("GET", endpoint, params=params)
        for _ in range(1, page):
            next_url = self._extract_next_url(response)
            if not next_url:
                return []
            response = await self._make_response("GET", next_url)

        if response.status_code == 204 or not response.content:
            return []
        return response.json()

    async def _get_all_pages(
        self,
        endpoint: str,
        params: Dict[str, Any],
        max_records: int,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        response = await self._make_response("GET", endpoint, params=params)

        while True:
            if response.content:
                batch = response.json()
                results.extend(batch)
                if len(results) >= max_records:
                    return results[:max_records]

            next_url = self._extract_next_url(response)
            if not next_url:
                return results

            response = await self._make_response("GET", next_url)

    async def list_jobs(
        self,
        per_page: int = 50,
        page: int = 1,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        self._add_date_filters(
            params, "created_at", after=created_after, before=created_before
        )
        if status:
            params["status"] = status

        return await self._get_paginated_page("jobs", params=params, page=page)

    async def list_all_jobs(
        self,
        per_page: int = 500,
        max_records: int = 2000,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        self._add_date_filters(
            params, "created_at", after=created_after, before=created_before
        )
        if status:
            params["status"] = status

        return await self._get_all_pages("jobs", params=params, max_records=max_records)

    async def get_job(self, job_id: int) -> Dict[str, Any]:
        jobs = await self._get_paginated_page(
            "jobs", params={"ids": str(job_id), "per_page": 1}, page=1
        )
        if not jobs:
            raise ValueError(f"Job {job_id} was not found")
        return jobs[0]

    async def list_candidates(
        self,
        per_page: int = 50,
        page: int = 1,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        email: Optional[str] = None,
        candidate_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        self._add_date_filters(
            params, "created_at", after=created_after, before=created_before
        )
        if email:
            params["email"] = email
        ids = self._ids_param(candidate_ids)
        if ids:
            params["ids"] = ids

        return await self._get_paginated_page("candidates", params=params, page=page)

    async def list_all_candidates(
        self,
        per_page: int = 500,
        max_records: int = 2000,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        email: Optional[str] = None,
        candidate_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        self._add_date_filters(
            params, "created_at", after=created_after, before=created_before
        )
        if email:
            params["email"] = email
        ids = self._ids_param(candidate_ids)
        if ids:
            params["ids"] = ids

        return await self._get_all_pages(
            "candidates", params=params, max_records=max_records
        )

    async def get_candidate(self, candidate_id: int) -> Dict[str, Any]:
        candidates = await self.list_candidates(
            per_page=1, page=1, candidate_ids=[candidate_id]
        )
        if not candidates:
            raise ValueError(f"Candidate {candidate_id} was not found")
        return candidates[0]

    async def create_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._make_request("POST", "candidates", json_data=candidate_data)

    async def update_candidate(
        self, candidate_id: int, candidate_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self._make_request(
            "PATCH", f"candidates/{candidate_id}", json_data=candidate_data
        )

    async def list_applications(
        self,
        per_page: int = 50,
        page: int = 1,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        job_id: Optional[int] = None,
        candidate_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        self._add_date_filters(
            params, "created_at", after=created_after, before=created_before
        )
        if job_id:
            params["job_ids"] = str(job_id)
        if candidate_id:
            params["candidate_ids"] = str(candidate_id)
        if status:
            params["status"] = status

        return await self._get_paginated_page("applications", params=params, page=page)

    async def list_all_applications(
        self,
        per_page: int = 500,
        max_records: int = 2000,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        job_id: Optional[int] = None,
        candidate_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        self._add_date_filters(
            params, "created_at", after=created_after, before=created_before
        )
        if job_id:
            params["job_ids"] = str(job_id)
        if candidate_id:
            params["candidate_ids"] = str(candidate_id)
        if status:
            params["status"] = status

        return await self._get_all_pages(
            "applications", params=params, max_records=max_records
        )

    async def get_application(self, application_id: int) -> Dict[str, Any]:
        applications = await self._get_paginated_page(
            "applications",
            params={"ids": str(application_id), "per_page": 1},
            page=1,
        )
        if not applications:
            raise ValueError(f"Application {application_id} was not found")
        return applications[0]

    async def advance_application(
        self, application_id: int, from_stage_id: int, to_stage_id: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {
            "from_stage_id": from_stage_id,
        }
        if to_stage_id:
            data["to_stage_id"] = to_stage_id

        return await self._make_request(
            "POST", f"applications/{application_id}/move", json_data=data
        )

    async def reject_application(
        self,
        application_id: int,
        rejection_reason_id: int,
        notes: Optional[str] = None,
        rejection_email: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {"rejection_reason_id": rejection_reason_id}
        if notes:
            data["notes"] = notes
        if rejection_email:
            data["rejection_email"] = rejection_email

        return await self._make_request(
            "POST", f"applications/{application_id}/reject", json_data=data
        )

    async def add_note_to_candidate(
        self, candidate_id: int, body: str, visibility: str = "private"
    ) -> Dict[str, Any]:
        data = {
            "candidate_id": candidate_id,
            "body": body,
            "visibility": visibility,
            "note_type": "NOTE",
        }
        return await self._make_request("POST", "notes", json_data=data)

    async def add_note_to_application(
        self, application_id: int, body: str, visibility: str = "private"
    ) -> Dict[str, Any]:
        application = await self.get_application(application_id)
        candidate_id = application.get("candidate_id")
        if not candidate_id:
            raise ValueError(
                f"Application {application_id} did not include candidate_id; "
                "cannot create v3 note"
            )

        data = {
            "candidate_id": candidate_id,
            "application_id": application_id,
            "body": body,
            "visibility": visibility,
            "note_type": "NOTE",
        }
        return await self._make_request("POST", "notes", json_data=data)

    async def list_departments(
        self, per_page: int = 50, page: int = 1
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        return await self._get_paginated_page("departments", params=params, page=page)

    async def list_offices(
        self, per_page: int = 50, page: int = 1
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        return await self._get_paginated_page("offices", params=params, page=page)

    async def list_users(
        self, per_page: int = 50, page: int = 1, email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {"per_page": per_page}
        if email:
            params["primary_email"] = email

        return await self._get_paginated_page("users", params=params, page=page)
