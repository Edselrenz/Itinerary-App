# Cloudflare Worker Reverse Proxy for Nueva Ecija Travel App

This Worker provides a **permanent, fixed HTTPS URL** (e.g. `https://nueva-ecija-api.<your-subdomain>.workers.dev`) that proxies incoming requests from GitHub Pages to your laptop's live backend.

Because `*.workers.dev` is hosted directly on Cloudflare's global anycast edge network, **it is 100% immune to Philippine ISP DNS blocks (PLDT, Converge, Globe, Smart) and home router NXDOMAIN caching**.

---

## 2-Minute Setup Guide (Via Cloudflare Web Dashboard)

No local Node.js or CLI tools required. You can deploy directly from your web browser:

1. **Log in to Cloudflare**:
   - Go to [dash.cloudflare.com](https://dash.cloudflare.com/) (create a free account if you don't have one).

2. **Create KV Namespace**:
   - In the left sidebar, click **Storage & Databases** &rarr; **KV**.
   - Click **Create a namespace**.
   - Name it: `TUNNEL_KV` and click **Add**.

3. **Create the Worker**:
   - In the left sidebar, click **Compute (Workers)** &rarr; **Workers & Pages**.
   - Click **Create application** &rarr; **Create Worker**.
   - Name it: `ne-itinerary-api` (or any name you like) &rarr; Click **Deploy**.

4. **Paste Worker Code**:
   - Click **Edit code** on your new Worker.
   - Replace all existing code with the contents of [`cloudflare-worker/worker.js`](./worker.js).
   - Click **Deploy** (top right).

5. **Bind KV & Add Secret Key**:
   - Go back to the Worker page &rarr; **Settings** &rarr; **Variables & Secrets**.
   - Under **KV Namespace Bindings**:
     - Click **Add binding**.
     - Variable name: `TUNNEL_KV`
     - KV namespace: Select `TUNNEL_KV` from the dropdown &rarr; Click **Save**.
   - Under **Environment Variables** (or Secrets):
     - Click **Add variable**.
     - Variable name: `ADMIN_SYNC_KEY`
     - Value: Choose any secret password (e.g., `my_secret_key_12345`) &rarr; Click **Save**.

6. **Configure Your Laptop (`.env`)**:
   - In your project root, open or create `.env` and add:
     ```env
     WORKER_SYNC_URL=https://ne-itinerary-api.<your-subdomain>.workers.dev
     WORKER_SYNC_KEY=my_secret_key_12345
     ```
   - Done! Whenever you run `start_server.bat` on your laptop, PowerShell will automatically push its newly generated tunnel URLs to this Worker.
   - GitHub Pages will connect to `https://ne-itinerary-api.<your-subdomain>.workers.dev/api/v1` automatically with zero user configuration!

---

## Alternative Setup (Via Wrangler CLI)

```bash
# 1. Login to Cloudflare
npx wrangler login

# 2. Create the KV namespace
npx wrangler kv:namespace create TUNNEL_KV

# 3. Copy the generated id into cloudflare-worker/wrangler.toml
# 4. Set the admin sync key secret
npx wrangler secret put ADMIN_SYNC_KEY

# 5. Deploy the worker
npx wrangler deploy
```

