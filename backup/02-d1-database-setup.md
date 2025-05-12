# 2. D1 Database Setup (30 mins)

## Create D1 Database

```bash
wrangler d1 create events_db
```

## Bind Database to Worker
Add to `wrangler.toml`:

```toml
[[d1_databases]]
binding = "EVENTS_DB"
database_name = "events_db"
database_id = "your-database-id"
```

## Define the Schema
Run the migration script:

## Migrate from Python to Cloudflare Workers

Follow the steps to transition your existing Python logic to Cloudflare Workers. This involves setting up the worker environment and migrating your code logic.

## Set Up Cloudflare D1

Ensure your worker is connected to Cloudflare D1 for database operations. Follow the instructions in the D1 Database Setup markdown.

## Implement Next.js Frontend

Create a Next.js frontend to interact with your worker and display data. Follow the instructions in the Frontend Setup markdown.

## Enable Cloudflare Analytics

Integrate Cloudflare Analytics to monitor and analyze traffic and performance.

## Testing & Debugging

Refer to the Testing & Debugging markdown for procedures to ensure everything is working correctly.

```bash
wrangler d1 execute events_db --command "
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT,
    location TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"
```