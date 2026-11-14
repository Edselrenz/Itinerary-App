export interface User {
  id: string;
  first_name: string;
  last_name: string;
  username_normalized: string;
  email_normalized: string;
  middle_initial?: string | null;
  phone_number?: string | null;
  birthday?: string | null;
  gender?: string | null;
  avatar_url?: string | null;
  default_daily_budget?: number | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  password: string;
  middle_initial?: string | null;
  phone_number?: string | null;
  birthday?: string | null;
  gender?: string | null;
  avatar_url?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UserUpdateRequest {
  first_name?: string;
  last_name?: string;
  username?: string;
  middle_initial?: string | null;
  phone_number?: string | null;
  birthday?: string | null;
  gender?: string | null;
  avatar_url?: string | null;
  default_daily_budget?: number | null;
  current_password?: string;
  new_password?: string;
}


