const resolveApiBaseUrl = (fallback: string): string => {
  if (typeof window !== 'undefined' && window.localStorage) {
    const custom = window.localStorage.getItem('ne_custom_api_url');
    if (custom && custom.trim()) {
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
  production: false,
  get apiBaseUrl(): string {
    return resolveApiBaseUrl('http://127.0.0.1:8000/api/v1');
  },
  tileUrlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  tileAttribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
  enableAppleAuth: false,
  googleClientId: 'dev-google-client-id.apps.googleusercontent.com',
};
