Here’s a **concise README and roadmap** to kickstart your vibe coding for the **event aggregation site**. This guide will help you leverage Cloudflare’s stack efficiently, with minimal friction.

---

## 📄 **README: Event Aggregation Site (Vibe Coding Edition)**

### **🚀 Objective:**

Build a lightweight event aggregation website using:

* **Cloudflare Workers:** For autoscraping and API handling.
* **Cloudflare D1:** To store event data.
* **Cloudflare Pages:** To host the frontend.

---

### **🛠️ Prerequisites:**

* Cloudflare account (with Workers and D1 access).
* Existing scrapers (preferably in Node.js or Python).
* Basic knowledge of JavaScript (for Workers).
* Cloudflare CLI installed (`wrangler`).

---

### **🗺️ Roadmap:**

#### **1. Project Setup (30 mins)**

1. **Install Wrangler:**

   ```
   npm install -g wrangler
   ```
2. **Login:**

   ```
   wrangler login
   ```
3. **Create a new Worker:**

   ```
   wrangler init event-aggregator
   cd event-aggregator
   ```

---

#### **2. D1 Database Setup (30 mins)**

1. **Create D1 Database:**

   ```
   wrangler d1 create events_db
   ```
2. **Bind Database to Worker:**
   Add to `wrangler.toml`:

   ```toml
   [[d1_databases]]
   binding = "EVENTS_DB"
   database_name = "events_db"
   database_id = "your-database-id"
   ```
3. **Define the Schema:**
   Run the migration script:

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

---

#### **3. Worker: Scraping Logic (1-2 hours)**

1. **Write the Worker:**
   Create a new file: `src/index.js`

   ```javascript
   export default {
     async fetch(request, env) {
       const url = new URL(request.url);
       if (url.pathname === "/scrape") {
         const response = await fetch("https://example.com/events");
         const text = await response.text();
         
         // Simple scraping example
         const eventMatches = text.matchAll(/<h2>(.*?)<\/h2>/g);
         const events = [...eventMatches].map(m => ({ title: m[1], date: "TBD" }));
         
         // Store in D1
         for (const event of events) {
           await env.EVENTS_DB.prepare(`
             INSERT INTO events (title, date, location, source_url) 
             VALUES (?, ?, ?, ?)
           `).bind(event.title, "TBD", "Unknown", "https://example.com/events").run();
         }

         return new Response("Scraped and stored!");
       }
       return new Response("Hello from Worker!");
     }
   };
   ```
2. **Deploy Worker:**

   ```
   wrangler deploy
   ```

---

#### **4. Automate Scraping (30 mins)**

1. **Add Cron Trigger:**
   Update `wrangler.toml`:

   ```toml
   [[triggers.crons]]
   schedule = "0 0 * * *" # Daily at midnight
   ```
2. **Deploy the updated worker:**

   ```
   wrangler deploy
   ```

---

#### **5. Frontend Setup (1-2 hours)**

1. **Create a Next.js project:**

   ```
   npx create-next-app@latest frontend
   cd frontend
   ```
2. **API Integration:**
   In `pages/index.js`:

   ```javascript
   export async function getServerSideProps() {
     const res = await fetch('https://your-worker-url/scrape');
     const data = await res.json();
     return { props: { events: data } };
   }

   export default function Home({ events }) {
     return (
       <div>
         <h1>Event Aggregator</h1>
         {events.map((event, index) => (
           <div key={index}>
             <h2>{event.title}</h2>
             <p>{event.date} - {event.location}</p>
           </div>
         ))}
       </div>
     );
   }
   ```
3. **Deploy with Cloudflare Pages:**

   ```
   wrangler pages publish ./frontend
   ```

---

#### **6. API Endpoint for Events (1 hour)**

Update `index.js` to handle event retrieval:

```javascript
if (url.pathname === "/events") {
  const { results } = await env.EVENTS_DB.prepare("SELECT * FROM events").all();
  return new Response(JSON.stringify(results), { headers: { "Content-Type": "application/json" } });
}
```

* **Test API:**

  ```
  curl https://your-worker-url/events
  ```

---

### **7. Testing & Debugging (1-2 hours)**

* Check **Worker Logs:**

  ```
  wrangler tail
  ```
* **Test Cron Jobs:**
  Manually trigger the worker to ensure scraping works.

---

### **8. Optional: Analytics and Monitoring**

* Enable **Cloudflare Analytics** to track traffic and API usage.
* Set up **error logging** within the Worker using `console.log()`.

---

### **🚧 Known Issues & Troubleshooting:**

1. **Worker Not Updating:**

   * Run `wrangler publish` again.
   * Check for syntax errors in logs.

2. **Cron Job Not Running:**

   * Make sure your cron syntax is correct.
   * Re-deploy the worker after adding the cron trigger.

3. **D1 Write Failures:**

   * Check database bindings in `wrangler.toml`.
   * Ensure your SQL syntax is correct.

---

### **📝 Future Improvements:**

1. **Enhanced Scraping:**

   * Use **Cheerio** in Workers for more robust parsing.
2. **Data Deduplication:**

   * Add checks to avoid duplicate entries.
3. **Advanced Filtering:**

   * Allow users to filter events by **date, location, or niche**.

---

