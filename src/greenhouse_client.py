import os
import base64
import asyncio
import time
from typing import Optional, Dict, Any, List
import httpx
from dotenv import load_dotenv

load_dotenv()


class GreenhouseClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GREENHOUSE_API_KEY")
        if not self.api_key:
            raise ValueError("Greenhouse API key is required")
        
        self.base_url = os.getenv("GREENHOUSE_BASE_URL", "https://harvest.greenhouse.io/v1")
        
        auth_string = base64.b64encode(f"{self.api_key}:".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
        }
        
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
            sleep_time = self._rate_limit_window - (current_time - self._last_request_time)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()

        self._request_count += 1
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=30.0
            )
            
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                await asyncio.sleep(retry_after)
                return await self._make_request(method, endpoint, params, json_data)
            
            response.raise_for_status()
            
            if response.status_code == 204:
                return {}
            
            return response.json()
    
    async def list_jobs(
        self, 
        per_page: int = 50, 
        page: int = 1,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {
            "per_page": per_page,
            "page": page,
        }
        if created_before:
            params["created_before"] = created_before
        if created_after:
            params["created_after"] = created_after
        if status:
            params["status"] = status
            
        return await self._make_request("GET", "jobs", params=params)
    
    async def get_job(self, job_id: int) -> Dict[str, Any]:
        return await self._make_request("GET", f"jobs/{job_id}")
    
    async def list_candidates(
        self, 
        per_page: int = 50,
        page: int = 1,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        email: Optional[str] = None,
        candidate_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        params = {
            "per_page": per_page,
            "page": page,
        }
        if created_before:
            params["created_before"] = created_before
        if created_after:
            params["created_after"] = created_after
        if email:
            params["email"] = email
        if candidate_ids:
            params["candidate_ids"] = ",".join(map(str, candidate_ids))
            
        return await self._make_request("GET", "candidates", params=params)
    
    async def get_candidate(self, candidate_id: int) -> Dict[str, Any]:
        return await self._make_request("GET", f"candidates/{candidate_id}")
    
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._make_request("POST", "candidates", json_data=candidate_data)
    
    async def update_candidate(self, candidate_id: int, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._make_request("PATCH", f"candidates/{candidate_id}", json_data=candidate_data)
    
    async def list_applications(
        self,
        per_page: int = 50,
        page: int = 1,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        job_id: Optional[int] = None,
        candidate_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {
            "per_page": per_page,
            "page": page,
        }
        if created_before:
            params["created_before"] = created_before
        if created_after:
            params["created_after"] = created_after
        if job_id:
            params["job_id"] = job_id
        if candidate_id:
            params["candidate_id"] = candidate_id
        if status:
            params["status"] = status
            
        return await self._make_request("GET", "applications", params=params)
    
    async def get_application(self, application_id: int) -> Dict[str, Any]:
        return await self._make_request("GET", f"applications/{application_id}")
    
    async def advance_application(
        self, 
        application_id: int, 
        from_stage_id: int,
        to_stage_id: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {
            "from_stage_id": from_stage_id,
        }
        if to_stage_id:
            data["to_stage_id"] = to_stage_id
            
        return await self._make_request(
            "POST", 
            f"applications/{application_id}/advance",
            json_data=data
        )
    
    async def reject_application(
        self,
        application_id: int,
        rejection_reason_id: Optional[int] = None,
        notes: Optional[str] = None,
        rejection_email_id: Optional[int] = None
    ) -> Dict[str, Any]:
        data = {}
        if rejection_reason_id:
            data["rejection_reason_id"] = rejection_reason_id
        if notes:
            data["notes"] = notes
        if rejection_email_id:
            data["rejection_email_send_email_at"] = rejection_email_id
            
        return await self._make_request(
            "POST",
            f"applications/{application_id}/reject",
            json_data=data
        )
    
    async def add_note_to_candidate(
        self,
        candidate_id: int,
        body: str,
        visibility: str = "private"
    ) -> Dict[str, Any]:
        data = {
            "body": body,
            "visibility": visibility
        }
        return await self._make_request(
            "POST",
            f"candidates/{candidate_id}/activity_feed/notes",
            json_data=data
        )
    
    async def add_note_to_application(
        self,
        application_id: int,
        body: str,
        visibility: str = "private"
    ) -> Dict[str, Any]:
        data = {
            "body": body,
            "visibility": visibility
        }
        return await self._make_request(
            "POST",
            f"applications/{application_id}/notes",
            json_data=data
        )
    
    async def list_departments(
        self,
        per_page: int = 50,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        params = {
            "per_page": per_page,
            "page": page,
        }
        return await self._make_request("GET", "departments", params=params)
    
    async def list_offices(
        self,
        per_page: int = 50,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        params = {
            "per_page": per_page,
            "page": page,
        }
        return await self._make_request("GET", "offices", params=params)
    
    async def list_users(
        self,
        per_page: int = 50,
        page: int = 1,
        email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {
            "per_page": per_page,
            "page": page,
        }
        if email:
            params["email"] = email
            
        return await self._make_request("GET", "users", params=params)