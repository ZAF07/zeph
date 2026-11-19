"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { SnapshotValueGroup } from "@/components/SnapshotValueGroup";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * What a run used, kept from when it started: the Platform Settings, the
 * Judge's settings and each case as it was. Loaded only when opened, since
 * it is long.
 *
 * @param props - `runId` is the run.
 * @returns The folded section.
 */
export function EvalRunSnapshotDetails({ runId }: { runId: string }) {
  const apiClient = useApiClient();
  const [isOpen, setIsOpen] = useState(false);
  const snapshotQuery = useQuery({
    queryKey: queryKeys.evalRunSnapshot(runId),
    queryFn: () => apiClient.getEvalRunSnapshot(runId),
    enabled: isOpen,
  });
  const snapshot = snapshotQuery.data;

  return (
    <details
      className="rounded-card border border-line bg-panel px-[18px] py-3.5 text-[14px] text-text"
      onToggle={(event) => setIsOpen(event.currentTarget.open)}
    >
      <summary className="cursor-pointer text-[15px] text-text">
        What this run used
      </summary>
      <div className="mt-3 flex flex-col gap-2">
        {snapshot === undefined ? (
          <p className="m-0 text-[13px] text-soft">
            {snapshotQuery.isError ? "Couldn’t load it." : "Loading…"}
          </p>
        ) : snapshot.settings === null ||
          snapshot.judge === null ||
          snapshot.cases === null ? (
          <p className="m-0 text-[13px] text-soft">
            Kept once the runner starts this run.
          </p>
        ) : (
          <>
            <p className="m-0 text-[13px] text-soft">
              As they were when the run started. Later changes never change
              these.
            </p>
            <SnapshotValueGroup
              title="Platform Settings"
              values={snapshot.settings}
            />
            <SnapshotValueGroup
              title="Judge settings"
              values={snapshot.judge}
            />
            <SnapshotValueGroup
              title={`Cases (${snapshot.cases.length})`}
              values={Object.fromEntries(
                snapshot.cases.map((item) => [item.key, item.content]),
              )}
            />
          </>
        )}
      </div>
    </details>
  );
}
