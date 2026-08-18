import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { AuthUser } from "../../types/auth";

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  hasHydrated: boolean;
  setHasHydrated: (hasHydrated: boolean) => void;
  setSession: (user: AuthUser, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      hasHydrated: false,
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
      setSession: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    {
      name: "ai-ride-auth",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    },
  ),
);
