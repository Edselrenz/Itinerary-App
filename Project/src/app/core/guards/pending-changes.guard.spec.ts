import { describe, it, expect, vi } from 'vitest';
import { pendingChangesGuard, ComponentCanDeactivate } from './pending-changes.guard';

describe('pendingChangesGuard', () => {
  it('should allow deactivation if component has no canDeactivate method', () => {
    const result = pendingChangesGuard({} as any, null as any, null as any, null as any);
    expect(result).toBe(true);
  });

  it('should return result of component canDeactivate method when returning boolean', () => {
    const mockComp: ComponentCanDeactivate = {
      canDeactivate: vi.fn().mockReturnValue(false),
    };
    const result = pendingChangesGuard(mockComp, null as any, null as any, null as any);
    expect(result).toBe(false);
    expect(mockComp.canDeactivate).toHaveBeenCalled();
  });

  it('should return promise from canDeactivate', async () => {
    const mockComp: ComponentCanDeactivate = {
      canDeactivate: vi.fn().mockResolvedValue(true),
    };
    const result = await pendingChangesGuard(mockComp, null as any, null as any, null as any);
    expect(result).toBe(true);
  });
});
