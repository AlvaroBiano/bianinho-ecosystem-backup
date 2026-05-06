---
name: buffer-api-connection
description: Connect to Buffer.com GraphQL API for social media management
---

# Buffer API Connection

## Overview
Connect to Buffer.com via their GraphQL API to manage social media accounts, view posts, and analyze performance.

## Connection Details

**API Endpoint:** `https://api.buffer.com`

**Authorization:** Bearer token in header
```bash
-H "Authorization: Bearer YOUR_API_KEY"
-H "Content-Type: application/json"
```

**API Key Location:** https://publish.buffer.com/settings/api

## Quick Test Query
```bash
curl -s -X POST 'https://api.buffer.com' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{"query": "{ account { id email name organizations { id name } } }"}'
```

## Key Queries

### Get Account and Organizations
```graphql
{
  account {
    id
    email
    name
    organizations {
      id
      name
    }
  }
}
```

### Get Channels (connected social accounts)
```graphql
{
  channels(input: { organizationId: "ORG_ID" }) {
    id
    service
  }
}
```

## What Buffer API CAN Do
- List connected social accounts (channels)
- View scheduled/published posts
- Create posts (with approved channels)
- View analytics/metrics
- Manage organization members

## What Buffer API CANNOT Do
- Search for new people/followers
- Access groups or group members
- Send direct messages
- Access accounts NOT connected to Buffer

## Notes
- Free plan: up to 3 channels, 10 posts/channel
- API is GraphQL (not REST)
- All queries require organizationId in input
- Buffer supports: Facebook, Instagram, TikTok, LinkedIn, Threads, Bluesky, YouTube, Pinterest, Google Business, Mastodon, X

## Comparison: Buffer vs Meta API

| Feature | Buffer API | Meta Graph API |
|---------|-----------|---------------|
| Setup difficulty | Easy (API key only) | Hard (App Review needed) |
| Groups access | No | No (restricted) |
| Member data | No | No (restricted) |
| Own posts/metrics | Yes | Yes |
| Publish posts | Yes | Yes |
| Free tier | Yes (3 channels) | Yes (basic) |
