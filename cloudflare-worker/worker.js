/**
 * Cloudflare Worker Reverse Proxy for Nueva Ecija Travel Itinerary
 * 
 * Provides a fixed, permanent HTTPS URL (*.workers.dev) for the GitHub Pages frontend,
 * dynamically proxying traffic to the developer laptop's active Cloudflare Tunnel
 * or ngrok tunnel stored in Cloudflare KV.
 */

const ALLOWED_ORIGINS = [
  'https://edselrenz.github.io',
  'http://localhost:4200',
  'http://localhost:8100',
  'http://localhost:8000',
  'capacitor://localhost',
];

function getCorsHeaders(request) {
  const requestOrigin = request.headers.get('Origin') || '';
  const allowOrigin = ALLOWED_ORIGINS.includes(requestOrigin)
    ? requestOrigin
    : 'https://edselrenz.github.io';

  return {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, ngrok-skip-browser-warning, X-Admin-Sync-Key',
    'Access-Control-Allow-Credentials': 'true',
    'Vary': 'Origin',
  };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const corsHeaders = getCorsHeaders(request);

    // Handle CORS preflight requests
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // 1. Admin sync endpoint called automatically by scripts/start_server.ps1
    if (url.pathname === '/__sync_tunnel' && request.method === 'POST') {
      const authKey = request.headers.get('X-Admin-Sync-Key');
      if (!env.ADMIN_SYNC_KEY || authKey !== env.ADMIN_SYNC_KEY) {
        return new Response(
          JSON.stringify({ error: 'Unauthorized: Invalid X-Admin-Sync-Key' }),
          { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      try {
        const body = await request.json();
        const payload = {
          cfUrl: body.cfUrl || null,
          ngrokUrl: body.ngrokUrl || 'https://anybody-cube-surprise.ngrok-free.dev',
          updatedAt: new Date().toISOString(),
        };

        if (env.TUNNEL_KV) {
          await env.TUNNEL_KV.put('ACTIVE_TUNNELS', JSON.stringify(payload));
        }

        return new Response(
          JSON.stringify({ status: 'synced', payload }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      } catch (err) {
        return new Response(
          JSON.stringify({ error: 'Invalid payload', details: String(err) }),
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }
    }

    // 2. Health & Status endpoint for the worker itself
    if (url.pathname === '/__status') {
      let stored = null;
      if (env.TUNNEL_KV) {
        stored = await env.TUNNEL_KV.get('ACTIVE_TUNNELS', { type: 'json' });
      }

      return new Response(
        JSON.stringify({
          status: 'ok',
          worker: 'nueva-ecija-api-proxy',
          active_tunnels: stored,
          timestamp: new Date().toISOString(),
        }),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // 3. Proxy API requests to active Cloudflare Tunnel first, falling back to ngrok
    let stored = null;
    if (env.TUNNEL_KV) {
      stored = await env.TUNNEL_KV.get('ACTIVE_TUNNELS', { type: 'json' });
    }

    const candidates = [
      stored?.cfUrl,
      stored?.ngrokUrl || 'https://anybody-cube-surprise.ngrok-free.dev',
    ].filter(Boolean);

    let lastError = null;
    for (const base of candidates) {
      try {
        const targetUrl = `${base.replace(/\/+$/, '')}${url.pathname}${url.search}`;
        const proxyHeaders = new Headers(request.headers);
        proxyHeaders.set('ngrok-skip-browser-warning', 'true');
        proxyHeaders.delete('Host');

        const upstreamRes = await fetch(targetUrl, {
          method: request.method,
          headers: proxyHeaders,
          body: ['GET', 'HEAD'].includes(request.method) ? null : request.body,
          redirect: 'follow',
        });

        // If upstream returns a valid response (including 4xx client errors like 404 or 401),
        // pass it through. Only retry/failover if it's 502/503/504 or ngrok is offline (ERR_NGROK_3200).
        const isNgrokOffline =
          upstreamRes.headers.get('ngrok-error-code') ||
          upstreamRes.headers.get('x-ngrok-error-code') ||
          (upstreamRes.status === 404 && (upstreamRes.headers.get('content-type') || '').includes('text/html'));

        if (upstreamRes.status < 500 && !isNgrokOffline) {
          const resHeaders = new Headers(upstreamRes.headers);
          Object.entries(corsHeaders).forEach(([k, v]) => resHeaders.set(k, v));
          return new Response(upstreamRes.body, {
            status: upstreamRes.status,
            headers: resHeaders,
          });
        }
      } catch (err) {
        lastError = err;
      }
    }

    // Both candidate tunnels failed or backend is offline
    return new Response(
      JSON.stringify({
        detail: 'Host laptop backend offline. Ensure start_server.bat is running.',
        candidates_tested: candidates,
        error: String(lastError),
      }),
      { status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  },
};

