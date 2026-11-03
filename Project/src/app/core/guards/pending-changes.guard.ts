import { CanDeactivateFn } from '@angular/router';

export interface ComponentCanDeactivate {
  canDeactivate: () => boolean | Promise<boolean>;
}

/**
 * Route guard that prevents travelers from accidentally abandoning unsaved
 * itinerary customizations in Custom Builder (UI-10).
 */
export const pendingChangesGuard: CanDeactivateFn<ComponentCanDeactivate> = (component) => {
  return component.canDeactivate ? component.canDeactivate() : true;
};
