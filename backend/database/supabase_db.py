import logging
import httpx
import json
from datetime import datetime, timezone
from typing import Any,List, Optional, Dict

logger = logging.getLogger('ats_resume_scorer')

from backend.core.config import SUPABASE_URL, SUPABASE_KEY

def _get_headers():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
def _get_rest_url(table: str) -> str:
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured.")

    return f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"


async def supabase_rest_get(
    table: str,
    params: Optional[Dict] = None,
) -> List[Dict]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError(
            "Supabase database configuration is not available."
        )

    url = _get_rest_url(table)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params=params or {},
            )

            response.raise_for_status()

            data = response.json()

            return data if isinstance(data, list) else []

    except Exception as exc:
        logger.error(
            f"Supabase GET failed for {table}: {exc}"
        )
        raise


async def supabase_rest_post(
    table: str,
    data: Any,
) -> List[Dict[str, Any]]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError(
            "Supabase database configuration is not available."
        )

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = _get_rest_url(table)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=data,
            )

            response.raise_for_status()

            result = response.json()

            return result if isinstance(result, list) else []

    except Exception as exc:
        logger.error(
            f"Supabase POST failed for {table}: {exc}"
        )
        raise


async def supabase_rest_patch(
    table: str,
    params: Dict,
    data: Dict,
) -> List[Dict]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError(
            "Supabase database configuration is not available."
        )

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = _get_rest_url(table)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=headers,
                params=params,
                json=data,
            )

            response.raise_for_status()

            result = response.json()

            return result if isinstance(result, list) else []

    except Exception as exc:
        logger.error(
            f"Supabase PATCH failed for {table}: {exc}"
        )
        raise
async def save_analysis(user_id: str, filename: str, analysis_result: Dict) -> Optional[str]:
    headers = _get_headers()
    if not headers:
        return None

    def _json_default(o):
        if hasattr(o, 'model_dump'):
            return o.model_dump()
        return str(o)
    serializable_result = json.loads(json.dumps(analysis_result, default=_json_default))

    doc = {
        "user_id": user_id,
        "filename": filename,
        "ats_score": serializable_result.get("ats_score", 0),
        "keyword_match": serializable_result.get("keyword_match", 0),
        "missing_keywords": serializable_result.get("missing_keywords", []),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis_result": serializable_result,
    }

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=doc)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                inserted_id = str(data[0].get("id"))
                logger.info(f"Saved analysis for user {user_id}: {inserted_id}")
                return inserted_id
            return None
    except Exception as exc:
        logger.error(f"Failed to save analysis to Supabase: {exc}")
        return None

async def get_user_history(user_id: str) -> List[Dict]:
    headers = _get_headers()
    if not headers:
        return []

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                headers=headers, 
                params={
                    "user_id": f"eq.{user_id}",
                    "order": "created_at.desc"
                }
            )
            response.raise_for_status()
            docs = response.json()
            
            results = []
            for doc in docs:
                results.append({
                    "id": str(doc.get("id")),
                    "filename": doc.get("filename", "resume"),
                    "resume_name": doc.get("filename", "resume"),
                    "job_title": "Software Engineer",
                    "ats_score": doc.get("ats_score", 0),
                    "keyword_match": doc.get("keyword_match", 0),
                    "missing_keywords": doc.get("missing_keywords", []),
                    "date": doc.get("created_at", ""),
                    "created_at": doc.get("created_at", ""),
                    "analysis_result": doc.get("analysis_result", {}),
                })
            return results
    except Exception as exc:
        logger.error(f"Failed to fetch history from Supabase: {exc}")
        return []

async def delete_analysis(analysis_id: str, user_id: str) -> bool:
    headers = _get_headers()
    if not headers:
        return False

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url, 
                headers=headers, 
                params={
                    "id": f"eq.{analysis_id}",
                    "user_id": f"eq.{user_id}"
                }
            )
            response.raise_for_status()
            return True
    except Exception as exc:
        logger.error(f"Failed to delete analysis {analysis_id}: {exc}")
        return False
async def get_user_profile(
    user_id: str,
) -> Optional[Dict]:
    headers = _get_headers()

    if not headers:
        return None

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                    "limit": "1",
                },
            )

            response.raise_for_status()

            data = response.json()

            if not data:
                return None

            return data[0]

    except Exception as exc:
        logger.error(
            f"Failed to fetch profile for {user_id}: {exc}"
        )
        return None


async def upsert_user_profile(
    user_id: str,
    username: str,
    skills: List[str],
    target_roles: List[str],
    experience: str,
    onboarding_completed: bool = False,
) -> Optional[Dict]:

    headers = _get_headers()

    if not headers:
        return None

    headers = {
        **headers,
        "Prefer": "resolution=merge-duplicates,return=representation",
    }

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"

    doc = {
        "user_id": user_id,
        "username": username,
        "skills": skills,
        "target_roles": target_roles,
        "experience": experience,
        "onboarding_completed": onboarding_completed,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=doc,
            )

            response.raise_for_status()

            data = response.json()

            if data:
                return data[0]

            return None

    except Exception as exc:
        logger.error(
            f"Failed to save profile for {user_id}: {exc}"
        )
        return None


async def update_profile_resume(
    user_id: str,
    filename: str,
    resume_text: str,
) -> Optional[Dict]:

    headers = _get_headers()

    if not headers:
        return None

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"

    doc = {
        "resume_filename": filename,
        "resume_text": resume_text,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                },
                json=doc,
            )

            response.raise_for_status()

            data = response.json()

            if data:
                return data[0]

            return None

    except Exception as exc:
        logger.error(
            f"Failed to save resume for {user_id}: {exc}"
        )
        return None


async def mark_onboarding_completed(
    user_id: str,
) -> Optional[Dict]:

    headers = _get_headers()

    if not headers:
        return None

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                },
                json={
                    "onboarding_completed": True,
                },
            )

            response.raise_for_status()

            data = response.json()

            if data:
                return data[0]

            return None

    except Exception as exc:
        logger.error(
            f"Failed to complete onboarding for {user_id}: {exc}"
        )
        return None
async def supabase_rest_get(
    table: str,
    params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError("Supabase database client is not available.")

    url = _get_rest_url(table)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=headers,
            params=params or {},
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            return data

        return []


async def supabase_rest_post(
    table: str,
    data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError("Supabase database client is not available.")

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = _get_rest_url(table)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=data,
        )

        response.raise_for_status()

        result = response.json()

        if isinstance(result, list):
            return result

        return []


async def supabase_rest_patch(
    table: str,
    params: Dict[str, Any],
    data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError("Supabase database client is not available.")

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = _get_rest_url(table)

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            url,
            headers=headers,
            params=params,
            json=data,
        )

        response.raise_for_status()

        result = response.json()

        if isinstance(result, list):
            return result

        return []