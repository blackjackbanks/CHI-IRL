# 5. Frontend Setup (1-2 hours)

## Create a Next.js project

```bash
npx create-next-app@latest frontend
cd frontend
```

## API Integration
In `pages/index.js`:

```javascript
export async function getServerSideProps() {
  const res = await fetch('https://your-worker-url/scrape');
  const data = await res.json();
  return { props: { events: data } };
}

export default function Home({ events }) {

## Migrate from Python to Cloudflare
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

## Deploy with Cloudflare Pages

```bash
wrangler pages publish ./frontend
```