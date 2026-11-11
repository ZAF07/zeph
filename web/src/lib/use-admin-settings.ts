"use client";

import { useCallback, useEffect, useState } from "react";

import type { AdminSettings, SettingValue } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

/** Where loading the admin settings stands. */
export type AdminSettingsState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; settings: AdminSettings };

/**
 * Loads the platform settings Admins edit, and saves changes to them. Every
 * admin settings page uses this, so each page only decides which settings it
 * shows.
 *
 * @returns The load state, `reload` to load again, and `save`, which saves
 *   new values and rejects if the backend refuses them.
 */
export function useAdminSettings(): {
  state: AdminSettingsState;
  reload: () => void;
  save: (values: Record<string, SettingValue>) => Promise<void>;
} {
  const apiClient = useApiClient();
  const [state, setState] = useState<AdminSettingsState>({ kind: "loading" });

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({
        kind: "loaded",
        settings: await apiClient.getAdminSettings(),
      });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = useCallback(
    async (values: Record<string, SettingValue>) => {
      const settings = await apiClient.updateAdminSettings(values);
      setState({ kind: "loaded", settings });
    },
    [apiClient],
  );

  return { state, reload: () => void load(), save };
}
