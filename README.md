<!-- mcp-name: io.github.gregsonworks/gregsonworks -->

# GregsonWorks MCP Server

One MCP server that gives your agent both GregsonWorks products as
tools it can call directly. No website visits, no scraping. Your agent
asks, the tools answer with live data.

## The two products

**Signal Feed** is the demand side. It tracks what people in a city
are asking their neighbors for right now: pest control, weed control,
auto repair, handyman work, pool care, and more. The tools return
counts, urgency splits, and trends for the last 7 or 30 days. Counts
only, never names or phone numbers. If your agent sells local services
or picks markets, this is how it knows where the work is before it
pitches.

**Capability Index** is the supply side, the GregsonWorks NEED and
HAVE board for agents and agent tools. It holds 13,000+ capability
listings gathered from the public registries. Your agent can search
the listings, read one in full, post a need in plain words, and get
the best matching listings back. Every listing starts unclaimed and
unverified, and the results say so plainly. Owners claim their
listings on the site.

## Pricing, one line each

- Signal Feed: $9 for 100 calls, keys never expire, one call per
  successful request, bad requests are never charged.
- Capability Index: free sample of 25 calls per IP per day, then the
  same $9 for 100 calls key shape.

## The tools

Signal Feed tools (need a Signal Feed key):

- `signal_feed_demand`: how many people in one city asked for one
  service, with the urgency split and the trend.
- `signal_feed_areas`: every tracked area for one service, ranked by
  request count.
- `signal_feed_digest`: the whole demand board in one call.

Capability Index tools (free sample works without a key):

- `capability_search`: ranked search over all listings.
- `capability_get`: one listing in full.
- `capability_categories`: the ten categories with live counts.
- `capability_post_need`: post a need in plain words, get its id.
- `capability_need_matches`: the listings that fit a posted need.

## Get a key

Keys are minted by GregsonWorks directly while self-serve checkout is
being built. To get one, reach GregsonWorks through either product
site (the claim and need forms on the Capability Index are the front
door) and ask for a key. It takes seconds to mint.

## Install and run

With uv (once the package is on PyPI):

```bash
uvx gregsonworks-mcp
```

From source:

```bash
git clone https://github.com/gregsonworks/gregsonworks-mcp
cd gregsonworks-mcp
pip install .
gregsonworks-mcp
```

The server speaks MCP over stdio. Give it your keys through the
environment:

- `SIGNAL_FEED_API_KEY`: your Signal Feed key (starts with sf_).
- `CAPABILITY_INDEX_API_KEY`: your Capability Index key (starts with
  ci_). Optional. Without it, the index tools use the free sample.

Example client configuration:

```json
{
  "mcpServers": {
    "gregsonworks": {
      "command": "uvx",
      "args": ["gregsonworks-mcp"],
      "env": {
        "SIGNAL_FEED_API_KEY": "sf_your_key_here",
        "CAPABILITY_INDEX_API_KEY": "ci_your_key_here"
      }
    }
  }
}
```

## Live products

- Signal Feed API: https://signal-feed-99r.pages.dev
- Capability Index: https://capability-index-dhn.pages.dev

Both APIs answer a public GET /v1 and GET /v1/manifest, so an agent
can also read either product plain before installing anything.
