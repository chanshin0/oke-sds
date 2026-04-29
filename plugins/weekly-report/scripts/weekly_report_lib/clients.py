"""Atlassian Cloud REST clients for weekly-report skills.

Token comes from macOS keychain (service='atlassian-api-token', account=email).
Email defaults to `git config user.email`, override with --email or
ATLASSIAN_EMAIL env var.
"""
from __future__ import annotations
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

KEYCHAIN_SERVICE = "atlassian-api-token"
RESOLVED_STATUSES = ("RESOLVE", "Done", "Closed", "완료", "해결됨")


def default_email() -> str:
    """Lookup chain: ATLASSIAN_EMAIL env → `git config sds.atlassian.email` → `git config user.email`."""
    if e := os.environ.get("ATLASSIAN_EMAIL"):
        return e
    for cfg in ("sds.atlassian.email", "user.email"):
        out = subprocess.run(["git", "config", cfg], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    return ""


def get_token(email: str) -> str:
    out = subprocess.run(
        ["security", "find-generic-password", "-a", email, "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(
            f"❌ no API token in macOS keychain for {email!r}.\n"
            f"   Run: security add-generic-password -a {email!r} -s {KEYCHAIN_SERVICE!r} -w 'YOUR_TOKEN' -U\n"
            f"   Get a token at https://id.atlassian.com/manage-profile/security/api-tokens"
        )
    return out.stdout.strip()


def _request(site: str, method: str, path: str, email: str, body: dict | None = None, params: dict | None = None) -> dict:
    url = f"https://{site}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    auth = base64.b64encode(f"{email}:{get_token(email)}".encode()).decode()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth}",
    }
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            text = resp.read()
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code} on {method} {url}\n{e.read().decode()}\n")
        raise


# ----- Confluence -----

def cf_get_page(site: str, page_id: str, email: str) -> dict:
    return _request(
        site, "GET", f"/wiki/rest/api/content/{page_id}", email,
        params={"expand": "body.storage,version,space,ancestors"},
    )


def cf_update_page(site: str, page_id: str, title: str, body_storage: str, new_version: int, email: str) -> dict:
    return _request(site, "PUT", f"/wiki/rest/api/content/{page_id}", email, body={
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {"number": new_version},
        "body": {"storage": {"value": body_storage, "representation": "storage"}},
    })


def cf_create_page(site: str, space_key: str, title: str, body_storage: str, parent_id: str, email: str) -> dict:
    return _request(site, "POST", "/wiki/rest/api/content", email, body={
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": body_storage, "representation": "storage"}},
    })


def cf_children(site: str, page_id: str, email: str, limit: int = 100) -> list[dict]:
    """List child pages of a Confluence page."""
    data = _request(
        site, "GET", f"/wiki/rest/api/content/{page_id}/child/page", email,
        params={"limit": str(limit)},
    )
    return data.get("results", [])


# ----- Jira -----

def jira_myself(site: str, email: str) -> dict:
    return _request(site, "GET", "/rest/api/3/myself", email)


def jira_search(site: str, jql: str, email: str, fields: str = "summary,status,updated", limit: int = 100) -> list[dict]:
    out: list[dict] = []
    next_token: str | None = None
    while True:
        params = {"jql": jql, "fields": fields, "maxResults": str(limit)}
        if next_token:
            params["nextPageToken"] = next_token
        data = _request(site, "GET", "/rest/api/3/search/jql", email, params=params)
        for issue in data.get("issues", []):
            f = issue["fields"]
            out.append({
                "key": issue["key"],
                "summary": f.get("summary", ""),
                "status": f["status"]["name"] if f.get("status") else "",
                "updated": f.get("updated", ""),
            })
        if data.get("isLast", True) or not data.get("nextPageToken"):
            break
        next_token = data["nextPageToken"]
    return out


def jira_done_recent(site: str, email: str, account_id: str | None = None, days: int = 8) -> list[dict]:
    """If account_id is None, uses currentUser()."""
    assignee = f'"{account_id}"' if account_id else "currentUser()"
    statuses = ", ".join(repr(s) for s in RESOLVED_STATUSES)
    jql = f'assignee = {assignee} AND status in ({statuses}) AND updated >= -{days}d ORDER BY updated DESC'
    return jira_search(site, jql, email)


def jira_active_or_todo(site: str, email: str, account_id: str | None = None) -> list[dict]:
    assignee = f'"{account_id}"' if account_id else "currentUser()"
    statuses = ", ".join(repr(s) for s in RESOLVED_STATUSES)
    jql = f'assignee = {assignee} AND sprint in openSprints() AND status not in ({statuses}) ORDER BY updated DESC'
    return jira_search(site, jql, email)
