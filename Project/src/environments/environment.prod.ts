const isTrustedApiHostname = (hostname: string): boolean => {
  const lower = hostname.toLowerCase();
  if (lower === 'localhost' || lower === '127.0.0.1') {
    return true;
  }
  if (
    lower === 'anybody-cube-surprise.ngrok-free.dev' ||
    lower.endsWith('.ngrok-free.dev') ||
    lower.endsWith('.ngrok.app') ||
    lower.endsWith('.ngrok.io') ||
    lower.endsWith('.trycloudflare.com') ||
    lower.endsWith('.workers.dev') ||
    lower.endsWith('.onrender.com') ||
    lower.endsWith('.koyeb.app')
  ) {
    return true;
  }
  return false;
};

const resolveApiBaseUrl = (fallback: string): string => {
  if (typeof window !== 'undefined' && window.localStorage) {
    const custom = window.localStorage.getItem('ne_custom_api_url');
    if (custom && custom.trim()) {
      let trimmed = custom.trim().replace(/\/+$/, '');
      if (!trimmed.endsWith('/api/v1')) {
        trimmed = `${trimmed}/api/v1`;
      }
      try {
        const parsed = new URL(trimmed);
        if (isTrustedApiHostname(parsed.hostname)) {
          return trimmed;
        } else {
          console.warn(`[Security] Untrusted custom API hostname rejected: ${parsed.hostname}`);
          window.localStorage.removeItem('ne_custom_api_url');
        }
      } catch {
        window.localStorage.removeItem('ne_custom_api_url');
      }
    }
  }
  return fallback;
};

export const environment = {
  production: true,
  get apiBaseUrl(): string {
    return resolveApiBaseUrl('https://incentive-fish-lung-observe.trycloudflare.com/api/v1');
  },
  tileUrlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  tileAttribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
  enableAppleAuth: false,
  googleClientId: 'prod-google-client-id.apps.googleusercontent.com',
};
