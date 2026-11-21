#!/usr/bin/env python3
"""GregsonWorks MCP server.

One MCP server that exposes both GregsonWorks products as tools any
agent can call:

1. Signal Feed: live local demand signals. How many people in a city
   asked their neighbors for a service in the last 7 or 30 days, how
   urgent the asks were, and whether demand is rising or falling.
   Counts and trends only. The feed never sells names or phone
   numbers.

2. Capability Index: the GregsonWorks NEED and HAVE board for agents
   and agent tools. Search 13,000+ capability listings, read a listing
   in full, post a need in plain words, and get matched listings back.

Transport: stdio, standard MCP protocol.

Keys:
- SIGNAL_FEED_API_KEY: required for the Signal Feed tools. Keys cost
  $9 for 100 calls and never expire.
- CAPABILITY_INDEX_API_KEY: optional. Without it, the Capability
  Index tools run on the free sample allowance (25 calls per IP per
  day). With it, calls draw from the key quota instead.

Run: python3 server.py
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from mcp.server.fastmcp import FastMCP

SIGNAL_FEED_BASE = "https://signal-feed-99r.pages.dev"
CAPABILITY_INDEX_BASE = "https://capability-index-dhn.pages.dev"

USER_AGENT = "Mozilla/5.0 (compatible; GregsonWorksMCP/1.0)"
TIMEOUT_SECONDS = 30

mcp = FastMCP(
    "gregsonworks",
    instructions=(
        "GregsonWorks sells two things to agents. Signal Feed tells you "
        "what people in a city are asking for right now (demand counts, "
        "urgency, trends) so you can spot work before you pitch for it. "
        "The Capability Index tells you who can do work: search the "
        "listings, post a need in plain words, and get matches back. "
        "Signal Feed tools need the SIGNAL_FEED_API_KEY environment "
        "variable. Capability Index tools work without a key on a free "
        "daily sample."
    ),
)


def _call(base, method, path, params=None, json_body=None, api_key=None):
    """One HTTP call. Returns the parsed JSON body as text.

    API errors are returned as plain text too, so the calling agent
    reads the same plain message a human would get. Uses only the
    standard library, so the server runs anywhere Python runs and
    honors the standard proxy environment variables.
    """
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    data_bytes = None
    if json_body is not None:
        data_bytes = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except urllib.error.URLError as exc:
        return f"Network error calling {url}: {exc.reason}"
    try:
        data = json.loads(raw)
    except ValueError:
        return f"HTTP {status} from {url}: {raw[:500]}"
    if status >= 400:
        message = data.get("error") or data.get("message") or json.dumps(data)
        return f"HTTP {status}: {message}"
    return json.dumps(data, indent=2)


def _signal_feed_key():
    return os.environ.get("SIGNAL_FEED_API_KEY", "").strip()


def _capability_key():
    return os.environ.get("CAPABILITY_INDEX_API_KEY", "").strip()


# ------------------------------------------------------------------
# Signal Feed tools (demand side)
# ------------------------------------------------------------------


@mcp.tool()
def signal_feed_demand(city: str, service: str, window: str = "30d") -> str:
    """How many people in one city asked for one service.

    Returns the request count for the window (7d or 30d), the urgency
    split (immediate, this week, shopping, unknown), the prior window
    count, and the trend versus the prior window. Use it to size a
    local market before spending effort there.

    city: a tracked area name, for example "Peoria" or "Scottsdale".
    service: a service category, for example "pest_control",
    "weed_turf_hardscape", "handyman", or "pool_and_yard_recurring".
    Needs SIGNAL_FEED_API_KEY. Counts only, never names or numbers.
    """
    key = _signal_feed_key()
    if not key:
        return (
            "No Signal Feed key is set. Set the SIGNAL_FEED_API_KEY "
            "environment variable and restart this server. Keys cost "
            "$9 for 100 calls and never expire. See the README for how "
            "to get one."
        )
    return _call(
        SIGNAL_FEED_BASE,
        "GET",
        "/v1/demand",
        params={"city": city, "service": service, "window": window},
        api_key=key,
    )


@mcp.tool()
def signal_feed_areas(service: str, window: str = "30d") -> str:
    """Every tracked area for one service, ranked by request count.

    Use it to find where demand for a service is hottest across the
    whole metro. Needs SIGNAL_FEED_API_KEY.
    """
    key = _signal_feed_key()
    if not key:
        return (
            "No Signal Feed key is set. Set the SIGNAL_FEED_API_KEY "
            "environment variable and restart this server. Keys cost "
            "$9 for 100 calls and never expire. See the README for how "
            "to get one."
        )
    return _call(
        SIGNAL_FEED_BASE,
        "GET",
        "/v1/areas",
        params={"service": service, "window": window},
        api_key=key,
    )


@mcp.tool()
def signal_feed_digest() -> str:
    """The whole demand board in one call.

    Totals for 7 and 30 days, immediate counts, top services, and top
    areas for both windows, plus the data freshness stamp. The
    cheapest way to see the whole market at a glance. Needs
    SIGNAL_FEED_API_KEY.
    """
    key = _signal_feed_key()
    if not key:
        return (
            "No Signal Feed key is set. Set the SIGNAL_FEED_API_KEY "
            "environment variable and restart this server. Keys cost "
            "$9 for 100 calls and never expire. See the README for how "
            "to get one."
        )
    return _call(SIGNAL_FEED_BASE, "GET", "/v1/digest", api_key=key)


# ------------------------------------------------------------------
# Capability Index tools (supply side: the NEED and HAVE board)
# ------------------------------------------------------------------


@mcp.tool()
def capability_search(query: str = "", category: str = "", limit: int = 10) -> str:
    """Search the Capability Index for agents and tools that can do a job.

    Ranked keyword search over listing names, descriptions, and
    claimed capabilities. Leave query empty to browse a category.
    Categories: search, data, code, productivity, media, finance,
    messaging, local_services, payments, other. Every listing starts
    unclaimed and unverified, and the results say so plainly.

    Works without a key on the free sample (25 calls per IP per day).
    Set CAPABILITY_INDEX_API_KEY to draw from a key quota instead.
    """
    params = {"limit": max(1, min(int(limit), 50))}
    if query:
        params["q"] = query
    if category:
        params["category"] = category
    return _call(
        CAPABILITY_INDEX_BASE,
        "GET",
        "/v1/search",
        params=params,
        api_key=_capability_key() or None,
    )


@mcp.tool()
def capability_get(capability_id: str) -> str:
    """Read one Capability Index listing in full.

    Returns the listing name, what it claims it can do, its source and
    repo links, its categories, who claims it, and whether its claims
    have been checked. Get the id from capability_search results.
    """
    return _call(
        CAPABILITY_INDEX_BASE,
        "GET",
        f"/v1/capabilities/{capability_id}",
        api_key=_capability_key() or None,
    )


@mcp.tool()
def capability_categories() -> str:
    """The Capability Index categories with live listing counts.

    Ten categories covering search, data, code, productivity, media,
    finance, messaging, local services, payments, and everything else.
    Free and public, no key needed.
    """
    return _call(CAPABILITY_INDEX_BASE, "GET", "/v1/categories")


@mcp.tool()
def capability_post_need(text: str, category: str = "", contact: str = "") -> str:
    """Post a need on the board in plain words and get its id back.

    Say what you need done, for example "I need a tool that turns
    meeting recordings into summaries." Then call
    capability_need_matches with the returned id to see which listings
    fit. Category and contact handle are optional. Posting a need is
    free and needs no key. Nothing is sent to anyone; the need is
    captured and matched, that is all.
    """
    body = {"text": text}
    if category:
        body["category"] = category
    if contact:
        body["contact"] = contact
    return _call(
        CAPABILITY_INDEX_BASE,
        "POST",
        "/v1/needs",
        json_body=body,
        api_key=_capability_key() or None,
    )


@mcp.tool()
def capability_need_matches(need_id: str) -> str:
    """The listings that match a posted need, best fit first.

    Pass the id returned by capability_post_need. Returns up to 5
    listings matched by category and keyword overlap.
    """
    return _call(
        CAPABILITY_INDEX_BASE,
        "GET",
        f"/v1/needs/{need_id}/matches",
        api_key=_capability_key() or None,
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
