/**
 * Global application state: the user session and their Layer-2 persistent
 * profile (identity, preferences, learned facts).
 *
 * Deliberately a SEPARATE store from chatStore: profile/preferences are
 * user-scoped and survive across every thread, so they must never live in —
 * or be cleared with — any individual conversation's state.
 */

import { create } from "zustand";
import { api } from "../api/client";

export const useUserStore = create((set, get) => ({
  user: null,      // { user_id, email, display_name }
  profile: null,   // UserProfileOut: { data: {identity, preferences, facts}, version }
  bootError: null,

  /** Establish the session and load the profile. Called once on app mount. */
  bootstrap: async () => {
    try {
      const user = await api.getSession();
      set({ user, bootError: null });
      await get().refreshProfile();
    } catch (err) {
      set({ bootError: String(err) });
    }
  },

  /** Re-fetch Layer 2 (the memory-extraction worker updates it after turns). */
  refreshProfile: async () => {
    const { user } = get();
    if (!user) return;
    try {
      const profile = await api.getProfile(user.user_id);
      set({ profile });
    } catch {
      // Non-fatal: the profile panel just shows the last known version.
    }
  },
}));
