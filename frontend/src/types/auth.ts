export type UserRole = "customer" | "driver" | "admin";
export type UserStatus = "active" | "inactive" | "suspended" | "pending_verification";

export interface AuthUser {
  id: string;
  email: string;
  phone_number: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface AuthResponse {
  user: AuthUser;
  tokens: TokenPair;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload extends LoginPayload {
  phone_number: string;
  full_name: string;
  role: UserRole;
}
