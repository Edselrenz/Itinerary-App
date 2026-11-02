const resolveApiBaseUrl = (fallback: string): string => {
  if (typeof window !== 'undefined' && window.localStorage) {
    const custom = window.localStorage.getItem('ne_custom_api_url');
    // Clear legacy ephemeral trycloudflare URL if present so app uses permanent ngrok tunnel
    if (custom && custom.includes('.trycloudflare.com')) {
      window.localStorage.removeItem('ne_custom_api_url');
    } else if (custom && custom.trim()) {
      let trimmed = custom.trim().replace(/\/+$/, '');
      if (!trimmed.endsWith('/api/v1')) {
        trimmed = `${trimmed}/api/v1`;
      }
      return trimmed;
    }
  }
  return fallback;
};

export const environment = {
  production: true,
  get apiBaseUrl(): string {
    return resolveApiBaseUrl('https://anybody-cube-surprise.ngrok-free.dev/api/v1');
  },
  tileUrlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  tileAttribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
  enableAppleAuth: false,
  googleClientId: 'prod-google-client-id.apps.googleusercontent.com',
};
