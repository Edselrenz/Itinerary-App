
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { importProvidersFrom, isDevMode, provideZoneChangeDetection } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';
import {
  PreloadAllModules,
  RouteReuseStrategy,
  provideRouter,
  withComponentInputBinding,
  withPreloading,
} from '@angular/router';
import { provideServiceWorker } from '@angular/service-worker';
import { IonicRouteStrategy, provideIonicAngular } from '@ionic/angular';
import { IonicStorageModule } from '@ionic/storage-angular';
import * as L from 'leaflet';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';
import { authInterceptor } from './app/core/interceptors/auth.interceptor';

if (typeof window !== 'undefined') {
  let leafletInstance: unknown = (L as unknown as { default?: unknown }).default ?? L;
  Object.defineProperty(window, 'L', {
    configurable: true,
    enumerable: true,
    get() {
      return leafletInstance;
    },
    set(newVal: unknown) {
      if (
        leafletInstance &&
        typeof (leafletInstance as { MarkerClusterGroup?: unknown }).MarkerClusterGroup !== 'undefined' &&
        newVal &&
        typeof (newVal as { MarkerClusterGroup?: unknown }).MarkerClusterGroup === 'undefined'
      ) {
        // Prevent destructive overwrites that strip plugin extensions (e.g. MarkerClusterGroup)
        Object.assign(leafletInstance as object, newVal as object);
      } else {
        leafletInstance = newVal;
      }
    },
  });
}

bootstrapApplication(AppComponent, {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    provideIonicAngular(),
    provideHttpClient(withInterceptors([authInterceptor])),
    importProvidersFrom(IonicStorageModule.forRoot()),
    provideRouter(routes, withPreloading(PreloadAllModules), withComponentInputBinding()),
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
  ],
});
