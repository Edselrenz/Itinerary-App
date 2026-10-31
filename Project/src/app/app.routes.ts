import type { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'welcome',
    loadComponent: () =>
      import('./features/auth/welcome/welcome.page').then((m) => m.WelcomePage),
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.page').then((m) => m.LoginPage),
  },
  {
    path: 'signup',
    loadComponent: () =>
      import('./features/auth/signup/signup.page').then((m) => m.SignupPage),
  },
  {
    path: 'guest',
    loadComponent: () =>
      import('./features/auth/guest/guest.page').then((m) => m.GuestPage),
  },
  {
    path: 'custom-builder',
    loadComponent: () =>
      import('./features/itinerary/custom-builder/custom-builder.page').then(
        (m) => m.CustomBuilderPage
      ),
  },
  {
    path: 'custom-builder/:id',
    loadComponent: () =>
      import('./features/itinerary/custom-builder/custom-builder.page').then(
        (m) => m.CustomBuilderPage
      ),
  },
  {
    path: 'suggested-wizard',
    loadComponent: () =>
      import('./features/itinerary/suggested-wizard/suggested-wizard.page').then(
        (m) => m.SuggestedWizardPage
      ),
  },
  {
    path: 'itinerary/:id',
    loadComponent: () =>
      import('./features/itinerary/itinerary-detail/itinerary-detail.page').then(
        (m) => m.ItineraryDetailPage
      ),
  },
  {
    path: 'tabs',
    loadChildren: () => import('./tabs/tabs.routes').then((m) => m.routes),
  },
  {
    path: '',
    redirectTo: '/welcome',
    pathMatch: 'full',
  },
  {
    path: '**',
    redirectTo: '/welcome',
  },
];
