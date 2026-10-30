import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthResponse, LoginRequest, RegisterRequest, User } from '../models/auth.models';
import { GuestStorageService } from './guest-storage.service';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private static readonly ACCESS_TOKEN_KEY = 'ne_access_token';
  private static readonly REFRESH_TOKEN_KEY = 'ne_refresh_token';
  private static readonly USER_KEY = 'ne_user_profile';

  private readonly currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$: Observable<User | null> = this.currentUserSubject.asObservable();

  constructor(
    private http: HttpClient,
    private guestStorage: GuestStorageService
  ) {
    this.loadStoredUser();
  }

  private loadStoredUser(): void {
    const rawUser = localStorage.getItem(AuthService.USER_KEY);
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
    return localStorage.getItem(AuthService.ACCESS_TOKEN_KEY);
  }

  public getRefreshToken(): string | null {
    return localStorage.getItem(AuthService.REFRESH_TOKEN_KEY);
  }

  public isAuthenticated(): boolean {
    return !!this.getAccessToken() && !!this.currentUserSubject.value;
  }

  public register(payload: RegisterRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${environment.apiBaseUrl}/auth/register`, payload)
      .pipe(tap((res) => this.handleAuthSuccess(res)));
  }

  public login(payload: LoginRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${environment.apiBaseUrl}/auth/login`, payload)
      .pipe(tap((res) => this.handleAuthSuccess(res)));
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
    return this.http.get<User>(`${environment.apiBaseUrl}/auth/me`).pipe(
      tap((user) => {
        localStorage.setItem(AuthService.USER_KEY, JSON.stringify(user));
        this.currentUserSubject.next(user);
      })
    );
  }

  private handleAuthSuccess(res: AuthResponse): void {
    localStorage.setItem(AuthService.ACCESS_TOKEN_KEY, res.access_token);
    localStorage.setItem(AuthService.REFRESH_TOKEN_KEY, res.refresh_token);
    localStorage.setItem(AuthService.USER_KEY, JSON.stringify(res.user));
    this.currentUserSubject.next(res.user);
    this.guestStorage.setGuestMode(false);
  }

  private clearAuthStorage(): void {
    localStorage.removeItem(AuthService.ACCESS_TOKEN_KEY);
    localStorage.removeItem(AuthService.REFRESH_TOKEN_KEY);
    localStorage.removeItem(AuthService.USER_KEY);
  }
}

