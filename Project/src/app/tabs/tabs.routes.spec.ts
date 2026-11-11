import { describe, it, expect } from 'vitest';

import { routes as appRoutes } from '../app.routes';

import { routes } from './tabs.routes';

describe('Routing & Redirect Gates (BUG-14 / TASK-12)', () => {
  it('should redirect /tabs/saved to history in tabs.routes', () => {
    const rootRoute = routes.find((r) => r.path === '');
    expect(rootRoute).toBeDefined();
    const savedRoute = rootRoute?.children?.find((r) => r.path === 'saved');
    expect(savedRoute).toBeDefined();
    expect(savedRoute?.redirectTo).toBe('history');
    expect(savedRoute?.pathMatch).toBe('full');
  });

  it('should redirect root /saved to /tabs/history in app.routes', () => {
    const savedRoute = appRoutes.find((r) => r.path === 'saved');
    expect(savedRoute).toBeDefined();
    expect(savedRoute?.redirectTo).toBe('/tabs/history');
    expect(savedRoute?.pathMatch).toBe('full');
  });

  it('should define all primary tab paths (home, map, history, profile)', () => {
    const rootRoute = routes.find((r) => r.path === '');
    const paths = rootRoute?.children?.map((c) => c.path) || [];
    expect(paths).toContain('home');
    expect(paths).toContain('map');
    expect(paths).toContain('history');
    expect(paths).toContain('profile');
    expect(paths).toContain('saved');
    expect(paths).toContain('favorites');
  });

  it('Phase 44.2: should configure favorites route redirect to profile with view=favorites', () => {
    const rootRoute = routes.find((r) => r.path === '');
    const favRoute = rootRoute?.children?.find((r) => r.path === 'favorites');
    expect(favRoute).toBeDefined();
    expect(typeof favRoute?.redirectTo).toBe('function');
    expect(favRoute?.pathMatch).toBe('full');
  });
});
