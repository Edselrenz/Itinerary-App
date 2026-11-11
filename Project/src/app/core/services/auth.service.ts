import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import type { Observable } from 'rxjs';
import { BehaviorSubject, catchError, of, tap, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  UserUpdateRequest,
} from '../models/auth.models';

import { ConnectivityService } from './connectivity.service';
import { GuestStorageService } from './guest-storage.service';
import { SecureTokenStorageService } from './secure-token-storage.service';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private connectivityService = inject(ConnectivityService, { optional: true });

  private get apiBaseUrl(): string {
    return this.connectivityService?.activeApiBaseUrl || environment.apiBaseUrl;
  }

  private static readonly ACCESS_TOKEN_KEY = 'ne_access_token';
  private static readonly REFRESH_TOKEN_KEY = 'ne_refresh_token';
  private static readonly USER_KEY = 'ne_user_profile';

  private readonly currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$: Observable<User | null> = this.currentUserSubject.asObservable();

  private http = inject(HttpClient);
  private guestStorage = inject(GuestStorageService);
  private secureTokenStorage = inject(SecureTokenStorageService);

  constructor() {
    this.secureTokenStorage.init();
    this.loadStoredUser();
  }

  private loadStoredUser(): void {
    const rawUser =
      localStorage.getItem(AuthService.USER_KEY) ||
      sessionStorage.getItem(AuthService.USER_KEY);
    const token = this.getAccessToken();
    if (rawUser && token) {
      try {
        this.currentUserSubject.next(JSON.parse(rawUser));
      } catch {
        this.logout();
      }
    }
  }

  public getAccessToken(): string | null {
    return this.secureTokenStorage.getAccessTokenSync();
  }

  public getRefreshToken(): string | null {
    return this.secureTokenStorage.getRefreshTokenSync();
  }

  private isTokenExpired(token: string): boolean {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return true;
      const base64Url = parts[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(jsonPayload);
      if (typeof payload.exp !== 'number') return false;
      return Date.now() >= payload.exp * 1000 - 5000;
    } catch {
      return true;
    }
  }

  public isAuthenticated(): boolean {
    const token = this.getAccessToken();
    const hasUser = !!this.currentUserSubject.value;
    if (!token || !hasUser) return false;
    if (!this.isTokenExpired(token)) return true;
    const refreshToken = this.getRefreshToken();
    return !!refreshToken && !this.isTokenExpired(refreshToken);
  }

  public isAccessTokenExpired(): boolean {
    const token = this.getAccessToken();
    if (!token) return true;
    return this.isTokenExpired(token);
  }

  public refreshSession(): Observable<AuthResponse> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      this.logout();
      return throwError(() => new Error('No refresh token available'));
    }
    return this.http
      .post<AuthResponse>(`${this.apiBaseUrl}/auth/refresh`, {
        refresh_token: refreshToken,
      })
      .pipe(
        tap((res) => {
          this.handleAuthSuccess(res);
        }),
        catchError((err) => {
          this.logout();
          return throwError(() => err);
        })
      );
  }

  public register(payload: RegisterRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.apiBaseUrl}/auth/register`, payload)
      .pipe(tap((res) => this.handleAuthSuccess(res, true)));
  }

  public login(payload: LoginRequest, rememberMe = true): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.apiBaseUrl}/auth/login`, payload)
      .pipe(
        tap((res) => this.handleAuthSuccess(res, rememberMe)),
        catchError((err) => {
          return throwError(() => err);
        })
      );
  }

  public loginDemo(rememberMe = true): Observable<AuthResponse> {
    const demoResponse: AuthResponse = {
      access_token: this.createDemoJwt('loverrukk@gmail.com'),
      refresh_token: this.createDemoJwt('loverrukk@gmail.com'),
      token_type: 'bearer',
      user: {
        id: 'usr_pattranite_demo_01',
        email_normalized: 'loverrukk@gmail.com',
        username_normalized: 'loverrukk',
        first_name: 'Pattranite',
        last_name: 'Limpatiyakorn',
        is_active: true,
        created_at: '2026-05-23T00:00:00Z',
      },
    };
    this.handleAuthSuccess(demoResponse, rememberMe);
    return of(demoResponse);
  }

  public isDemoUser(): boolean {
    const user = this.currentUserSubject.value;
    return user?.id === 'usr_pattranite_demo_01' || user?.username_normalized === 'loverrukk';
  }

  private createDemoJwt(email = 'loverrukk@gmail.com'): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(
      JSON.stringify({
        sub: 'usr_pattranite_demo_01',
        email,
        role: 'traveler',
        exp: Math.floor(Date.now() / 1000) + 86400 * 30,
      })
    );
    const signature = btoa('demo_signature');
    return `${header}.${payload}.${signature}`;
  }

  public async continueAsGuest(): Promise<void> {
    this.clearAuthStorage();
    this.currentUserSubject.next(null);
    await this.guestStorage.setGuestMode(true);
  }

  public async logout(): Promise<void> {
    this.clearAuthStorage();
    this.currentUserSubject.next(null);
    await this.guestStorage.setGuestMode(false);
  }

  public getProfile(): Observable<User> {
    return this.http.get<User>(`${this.apiBaseUrl}/auth/me`).pipe(
      tap((user) => {
        const storage = sessionStorage.getItem(AuthService.ACCESS_TOKEN_KEY)
          ? sessionStorage
          : localStorage;
        storage.setItem(AuthService.USER_KEY, JSON.stringify(user));
        this.currentUserSubject.next(user);
      })
    );
  }

  public updateProfile(payload: UserUpdateRequest): Observable<User> {
    return this.http.patch<User>(`${this.apiBaseUrl}/auth/me`, payload).pipe(
      tap((user) => {
        const storage = sessionStorage.getItem(AuthService.ACCESS_TOKEN_KEY)
          ? sessionStorage
          : localStorage;
        storage.setItem(AuthService.USER_KEY, JSON.stringify(user));
        this.currentUserSubject.next(user);
      })
    );
  }

  private handleAuthSuccess(res: AuthResponse, rememberMe = true): void {
    this.clearAuthStorage();
    this.secureTokenStorage.saveTokens(res.access_token, res.refresh_token, rememberMe);
    const storage: Storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem(AuthService.USER_KEY, JSON.stringify(res.user));
    this.currentUserSubject.next(res.user);
    this.guestStorage.setGuestMode(false);
  }

  private clearAuthStorage(): void {
    this.secureTokenStorage.clearTokens();
    localStorage.removeItem(AuthService.USER_KEY);
    sessionStorage.removeItem(AuthService.USER_KEY);
  }
}
