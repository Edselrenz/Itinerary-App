import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { WelcomePage } from './welcome.page';

describe('WelcomePage', () => {
  let component: WelcomePage;
  let fixture: ComponentFixture<WelcomePage>;

  const mockRouter = {
    navigate: vi.fn().mockResolvedValue(true),
    url: '/welcome',
  };

  const mockActivatedRoute = {
    queryParams: of({ loggedOut: 'false' }),
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [WelcomePage],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: ActivatedRoute, useValue: mockActivatedRoute },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(WelcomePage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the welcome page component in default onboarding state', () => {
    expect(component).toBeTruthy();
    expect(component.isAfterLogout).toBe(false);
  });

  it('renders After Log Out state when queryParam loggedOut is true', async () => {
    const routeWithLogout = {
      queryParams: of({ loggedOut: 'true' }),
    };

    const logoutFixture = TestBed.createComponent(WelcomePage);
    const logoutComp = logoutFixture.componentInstance;
    (logoutComp as any).route = routeWithLogout;
    logoutComp.ngOnInit();
    logoutFixture.detectChanges();

    expect(logoutComp.isAfterLogout).toBe(true);
  });

  it('navigates to /login when goToLogin is called', () => {
    component.goToLogin();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('navigates to /signup when goToSignup is called', () => {
    component.goToSignup();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/signup']);
  });

  it('navigates to /guest when goToGuest is called', () => {
    component.goToGuest();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/guest']);
  });
});
