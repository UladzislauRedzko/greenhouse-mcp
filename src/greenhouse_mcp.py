#!/usr/bin/env python3
import os
import json
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP, Context
from dotenv import load_dotenv

from .greenhouse_client import GreenhouseClient
from .models import (
    Job, Candidate, Application, Note,
    CandidateCreateRequest, ApplicationAdvanceRequest
)

load_dotenv()

mcp = FastMCP("Greenhouse API 🌱")
mcp.description = "MCP server for interacting with Greenhouse Harvest API"

client: Optional[GreenhouseClient] = None


def get_client() -> GreenhouseClient:
    global client
    if client is None:
        api_key = os.getenv("GREENHOUSE_API_KEY")
        if not api_key:
            raise ValueError(
                "GREENHOUSE_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
        client = GreenhouseClient(api_key)
    return client


@mcp.tool
async def list_jobs(
    per_page: int = 50,
    page: int = 1,
    status: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    List all jobs in Greenhouse.
    
    Args:
        per_page: Number of results per page (max 500)
        page: Page number to retrieve
        status: Filter by job status (open, closed, draft)
        created_after: ISO 8601 date to filter jobs created after
        created_before: ISO 8601 date to filter jobs created before
    
    Returns:
        List of job objects
    """
    try:
        gh_client = get_client()
        jobs = await gh_client.list_jobs(
            per_page=per_page,
            page=page,
            status=status,
            created_after=created_after,
            created_before=created_before
        )
        if ctx:
            ctx.info(f"Retrieved {len(jobs)} jobs")
        return jobs
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list jobs: {str(e)}")
        raise


@mcp.tool
async def get_job(
    job_id: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific job.
    
    Args:
        job_id: The ID of the job to retrieve
    
    Returns:
        Job object with full details
    """
    try:
        gh_client = get_client()
        job = await gh_client.get_job(job_id)
        if ctx:
            ctx.info(f"Retrieved job: {job.get('name', 'Unknown')}")
        return job
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get job {job_id}: {str(e)}")
        raise


@mcp.tool
async def list_candidates(
    per_page: int = 50,
    page: int = 1,
    email: Optional[str] = None,
    candidate_ids: Optional[List[int]] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    List candidates in Greenhouse.
    
    Args:
        per_page: Number of results per page (max 500)
        page: Page number to retrieve
        email: Filter by candidate email address
        candidate_ids: List of specific candidate IDs to retrieve
        created_after: ISO 8601 date to filter candidates created after
        created_before: ISO 8601 date to filter candidates created before
    
    Returns:
        List of candidate objects
    """
    try:
        gh_client = get_client()
        candidates = await gh_client.list_candidates(
            per_page=per_page,
            page=page,
            email=email,
            candidate_ids=candidate_ids,
            created_after=created_after,
            created_before=created_before
        )
        if ctx:
            ctx.info(f"Retrieved {len(candidates)} candidates")
        return candidates
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list candidates: {str(e)}")
        raise


@mcp.tool
async def get_candidate(
    candidate_id: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific candidate.
    
    Args:
        candidate_id: The ID of the candidate to retrieve
    
    Returns:
        Candidate object with full details
    """
    try:
        gh_client = get_client()
        candidate = await gh_client.get_candidate(candidate_id)
        if ctx:
            name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}"
            ctx.info(f"Retrieved candidate: {name.strip() or 'Unknown'}")
        return candidate
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get candidate {candidate_id}: {str(e)}")
        raise


@mcp.tool
async def create_candidate(
    first_name: str,
    last_name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a new candidate in Greenhouse.
    
    Args:
        first_name: Candidate's first name
        last_name: Candidate's last name
        email: Candidate's email address
        phone: Candidate's phone number
        company: Current company
        title: Current job title
        tags: List of tags to apply to the candidate
    
    Returns:
        Created candidate object
    """
    try:
        gh_client = get_client()
        
        candidate_data = {
            "first_name": first_name,
            "last_name": last_name,
        }
        
        if email:
            candidate_data["email_addresses"] = [
                {"value": email, "type": "personal"}
            ]
        
        if phone:
            candidate_data["phone_numbers"] = [
                {"value": phone, "type": "mobile"}
            ]
        
        if company:
            candidate_data["company"] = company
        
        if title:
            candidate_data["title"] = title
        
        if tags:
            candidate_data["tags"] = tags
        
        candidate = await gh_client.create_candidate(candidate_data)
        
        if ctx:
            ctx.info(f"Created candidate: {first_name} {last_name}")
        
        return candidate
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to create candidate: {str(e)}")
        raise


@mcp.tool
async def update_candidate(
    candidate_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Update an existing candidate in Greenhouse.
    
    Args:
        candidate_id: ID of the candidate to update
        first_name: Updated first name
        last_name: Updated last name
        email: Updated email address
        phone: Updated phone number
        company: Updated company
        title: Updated job title
        tags: Updated list of tags
    
    Returns:
        Updated candidate object
    """
    try:
        gh_client = get_client()
        
        update_data = {}
        
        if first_name:
            update_data["first_name"] = first_name
        
        if last_name:
            update_data["last_name"] = last_name
        
        if email:
            update_data["email_addresses"] = [
                {"value": email, "type": "personal"}
            ]
        
        if phone:
            update_data["phone_numbers"] = [
                {"value": phone, "type": "mobile"}
            ]
        
        if company:
            update_data["company"] = company
        
        if title:
            update_data["title"] = title
        
        if tags:
            update_data["tags"] = tags
        
        candidate = await gh_client.update_candidate(candidate_id, update_data)
        
        if ctx:
            ctx.info(f"Updated candidate ID: {candidate_id}")
        
        return candidate
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to update candidate {candidate_id}: {str(e)}")
        raise


@mcp.tool
async def list_applications(
    per_page: int = 50,
    page: int = 1,
    job_id: Optional[int] = None,
    candidate_id: Optional[int] = None,
    status: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    List applications in Greenhouse.
    
    Args:
        per_page: Number of results per page (max 500)
        page: Page number to retrieve
        job_id: Filter by job ID
        candidate_id: Filter by candidate ID
        status: Filter by application status
        created_after: ISO 8601 date to filter applications created after
        created_before: ISO 8601 date to filter applications created before
    
    Returns:
        List of application objects
    """
    try:
        gh_client = get_client()
        applications = await gh_client.list_applications(
            per_page=per_page,
            page=page,
            job_id=job_id,
            candidate_id=candidate_id,
            status=status,
            created_after=created_after,
            created_before=created_before
        )
        has_more = len(applications) == per_page
        if ctx:
            ctx.info(f"Retrieved {len(applications)} applications" + (" (more pages available)" if has_more else ""))
        return {
            "results": applications,
            "count": len(applications),
            "page": page,
            "per_page": per_page,
            "has_more": has_more,
            "warning": "Results may be truncated. Use 'page' parameter to retrieve more." if has_more else None,
        }
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list applications: {str(e)}")
        raise


@mcp.tool
async def list_all_applications(
    job_id: Optional[int] = None,
    candidate_id: Optional[int] = None,
    status: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    max_records: int = 2000,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Fetch ALL applications across all pages automatically.
    Use this for analytics and reporting to avoid pagination truncation.

    Args:
        job_id: Filter by job ID
        candidate_id: Filter by candidate ID
        status: Filter by application status
        created_after: ISO 8601 date — REQUIRED for date-bounded queries
        created_before: ISO 8601 date to filter applications created before
        max_records: Safety limit on total records fetched (default 2000)

    Returns:
        All matching applications with total count and date range metadata
    """
    try:
        gh_client = get_client()
        all_results = []
        page = 1

        while len(all_results) < max_records:
            batch = await gh_client.list_applications(
                per_page=250,
                page=page,
                job_id=job_id,
                candidate_id=candidate_id,
                status=status,
                created_after=created_after,
                created_before=created_before,
            )
            all_results.extend(batch)
            if ctx:
                ctx.info(f"Fetched page {page} ({len(batch)} records, {len(all_results)} total)")
            if len(batch) < 250:
                break
            page += 1

        dates = [r["applied_at"] for r in all_results if r.get("applied_at")]
        return {
            "results": all_results,
            "count": len(all_results),
            "date_range": {"earliest": min(dates), "latest": max(dates)} if dates else None,
            "truncated": len(all_results) >= max_records,
        }
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to fetch all applications: {str(e)}")
        raise


@mcp.tool
async def sourcing_report(
    created_after: str,
    created_before: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Generate a sourcing activity report for a given date range.
    Automatically fetches all pages across all jobs and aggregates by sourcer and job.
    Use this instead of list_all_applications for weekly/monthly reports.

    Args:
        created_after: ISO 8601 start date, e.g. "2026-06-24T00:00:00.000Z"
        created_before: ISO 8601 end date, e.g. "2026-06-30T23:59:59.000Z"

    Returns:
        Aggregated sourcing stats by sourcer and by job
    """
    try:
        gh_client = get_client()

        jobs = await gh_client.list_jobs(per_page=500, status="open")
        job_names = {j["id"]: j["name"] for j in jobs}

        by_sourcer: Dict[str, Any] = {}
        by_job: Dict[str, Any] = {}
        total = 0

        for job_id, job_name in job_names.items():
            page = 1
            while True:
                batch = await gh_client.list_applications(
                    per_page=250,
                    page=page,
                    job_id=job_id,
                    created_after=created_after,
                    created_before=created_before,
                )
                for app in batch:
                    total += 1
                    credited = app.get("credited_to") or {}
                    sourcer = f"{credited.get('first_name', '')} {credited.get('last_name', '')}".strip() or "Unknown"

                    if sourcer not in by_sourcer:
                        by_sourcer[sourcer] = {"total": 0, "by_job": {}}
                    by_sourcer[sourcer]["total"] += 1
                    by_sourcer[sourcer]["by_job"][job_name] = by_sourcer[sourcer]["by_job"].get(job_name, 0) + 1

                    if job_name not in by_job:
                        by_job[job_name] = {"total": 0, "by_sourcer": {}}
                    by_job[job_name]["total"] += 1
                    by_job[job_name]["by_sourcer"][sourcer] = by_job[job_name]["by_sourcer"].get(sourcer, 0) + 1

                if ctx:
                    ctx.info(f"{job_name}: page {page} ({len(batch)} records)")
                if len(batch) < 250:
                    break
                page += 1

        by_sourcer = dict(sorted(by_sourcer.items(), key=lambda x: x[1]["total"], reverse=True))
        by_job = dict(sorted(by_job.items(), key=lambda x: x[1]["total"], reverse=True))

        return {
            "period": {"from": created_after, "to": created_before},
            "total": total,
            "by_sourcer": by_sourcer,
            "by_job": by_job,
        }
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to generate sourcing report: {str(e)}")
        raise


@mcp.tool
async def get_application(
    application_id: int,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific application.
    
    Args:
        application_id: The ID of the application to retrieve
    
    Returns:
        Application object with full details
    """
    try:
        gh_client = get_client()
        application = await gh_client.get_application(application_id)
        if ctx:
            ctx.info(f"Retrieved application ID: {application_id}")
        return application
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to get application {application_id}: {str(e)}")
        raise


@mcp.tool
async def advance_application(
    application_id: int,
    from_stage_id: int,
    to_stage_id: Optional[int] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Advance an application to the next stage in the hiring process.
    
    Args:
        application_id: ID of the application to advance
        from_stage_id: Current stage ID (must match the application's current stage)
        to_stage_id: Target stage ID (if not provided, advances to next stage)
    
    Returns:
        Success confirmation
    """
    try:
        gh_client = get_client()
        result = await gh_client.advance_application(
            application_id=application_id,
            from_stage_id=from_stage_id,
            to_stage_id=to_stage_id
        )
        if ctx:
            ctx.info(f"Advanced application {application_id}")
        return result
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to advance application {application_id}: {str(e)}")
        raise


@mcp.tool
async def reject_application(
    application_id: int,
    rejection_reason_id: Optional[int] = None,
    notes: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Reject an application.
    
    Args:
        application_id: ID of the application to reject
        rejection_reason_id: ID of the rejection reason (optional)
        notes: Additional notes about the rejection (optional)
    
    Returns:
        Success confirmation
    """
    try:
        gh_client = get_client()
        result = await gh_client.reject_application(
            application_id=application_id,
            rejection_reason_id=rejection_reason_id,
            notes=notes
        )
        if ctx:
            ctx.info(f"Rejected application {application_id}")
        return result
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to reject application {application_id}: {str(e)}")
        raise


@mcp.tool
async def add_note_to_candidate(
    candidate_id: int,
    note: str,
    visibility: str = "private",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add a note to a candidate's activity feed.
    
    Args:
        candidate_id: ID of the candidate
        note: The note content
        visibility: Note visibility (admin_only, private, or public)
    
    Returns:
        Created note object
    """
    try:
        gh_client = get_client()
        result = await gh_client.add_note_to_candidate(
            candidate_id=candidate_id,
            body=note,
            visibility=visibility
        )
        if ctx:
            ctx.info(f"Added note to candidate {candidate_id}")
        return result
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to add note to candidate {candidate_id}: {str(e)}")
        raise


@mcp.tool
async def add_note_to_application(
    application_id: int,
    note: str,
    visibility: str = "private",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Add a note to an application.
    
    Args:
        application_id: ID of the application
        note: The note content
        visibility: Note visibility (admin_only, private, or public)
    
    Returns:
        Created note object
    """
    try:
        gh_client = get_client()
        result = await gh_client.add_note_to_application(
            application_id=application_id,
            body=note,
            visibility=visibility
        )
        if ctx:
            ctx.info(f"Added note to application {application_id}")
        return result
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to add note to application {application_id}: {str(e)}")
        raise


@mcp.tool
async def list_departments(
    per_page: int = 50,
    page: int = 1,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    List all departments in Greenhouse.
    
    Args:
        per_page: Number of results per page
        page: Page number to retrieve
    
    Returns:
        List of department objects
    """
    try:
        gh_client = get_client()
        departments = await gh_client.list_departments(
            per_page=per_page,
            page=page
        )
        if ctx:
            ctx.info(f"Retrieved {len(departments)} departments")
        return departments
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list departments: {str(e)}")
        raise


@mcp.tool
async def list_offices(
    per_page: int = 50,
    page: int = 1,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    List all offices in Greenhouse.
    
    Args:
        per_page: Number of results per page
        page: Page number to retrieve
    
    Returns:
        List of office objects
    """
    try:
        gh_client = get_client()
        offices = await gh_client.list_offices(
            per_page=per_page,
            page=page
        )
        if ctx:
            ctx.info(f"Retrieved {len(offices)} offices")
        return offices
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list offices: {str(e)}")
        raise


@mcp.tool
async def list_users(
    per_page: int = 50,
    page: int = 1,
    email: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """
    List users in Greenhouse.
    
    Args:
        per_page: Number of results per page
        page: Page number to retrieve
        email: Filter by user email address
    
    Returns:
        List of user objects
    """
    try:
        gh_client = get_client()
        users = await gh_client.list_users(
            per_page=per_page,
            page=page,
            email=email
        )
        if ctx:
            ctx.info(f"Retrieved {len(users)} users")
        return users
    except Exception as e:
        if ctx:
            ctx.error(f"Failed to list users: {str(e)}")
        raise


def main():
    """Main entry point for the MCP server."""
    import sys
    
    if not os.getenv("GREENHOUSE_API_KEY"):
        print("Error: GREENHOUSE_API_KEY environment variable is required", file=sys.stderr)
        print("Please set it in your .env file or environment.", file=sys.stderr)
        sys.exit(1)
    
    mcp.run()


if __name__ == "__main__":
    main()