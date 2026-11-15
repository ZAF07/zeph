"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  confirmDangerButton,
  dangerButton,
  secondaryButton,
} from "@/components/button-styles";
import type { EvalRun } from "@/lib/api-client";
import { countOf, isRunGoing } from "@/lib/evals";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * What an Admin can do with a run: Cancel it while it is Queued or Running,
 * Re-run its Fail and Error cases once it has ended, or delete it with its
 * results and traces after a confirm step.
 *
 * @param props - `run` is the run.
 * @returns The buttons that fit the run's state.
 */
export function EvalRunActions({ run }: { run: EvalRun }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const failedCount = run.failed + run.errored;
  const isGoing = isRunGoing(run.state);

  const cancelMutation = useMutation({
    mutationFn: () => apiClient.cancelEvalRun(run.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.evalRun(run.id),
      });
      void queryClient.invalidateQueries({ queryKey: queryKeys.allEvalRuns });
    },
  });
  const rerunMutation = useMutation({
    mutationFn: () => apiClient.rerunFailedCases(run.id),
    onSuccess: (rerun) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.allEvalRuns });
      router.push(`/admin/evals/runs/${rerun.id}`);
    },
  });
  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteEvalRun(run.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.allEvalRuns });
      router.push("/admin/evals");
    },
  });
  const failed =
    cancelMutation.isError || rerunMutation.isError || deleteMutation.isError;

  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex flex-wrap gap-2">
        {isGoing ? (
          <button
            type="button"
            className={secondaryButton}
            disabled={run.cancel_requested || cancelMutation.isPending}
            onClick={() => cancelMutation.mutate()}
          >
            {run.cancel_requested ? "Cancelling…" : "Cancel run"}
          </button>
        ) : null}
        {!isGoing && failedCount > 0 ? (
          <button
            type="button"
            className={secondaryButton}
            disabled={rerunMutation.isPending || rerunMutation.isSuccess}
            onClick={() => rerunMutation.mutate()}
          >
            Re-run failed · {countOf(failedCount, "case")}
          </button>
        ) : null}
        {run.state !== "running" && !isConfirmingDelete ? (
          <button
            type="button"
            className={dangerButton}
            onClick={() => setIsConfirmingDelete(true)}
          >
            Delete run
          </button>
        ) : null}
      </div>
      {isConfirmingDelete && run.state !== "running" ? (
        <div className="flex flex-col gap-3 rounded-card bg-danger-tint p-5">
          <p className="m-0 text-caption">
            This deletes the run with its Case Results and traces. It can’t be
            undone.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={confirmDangerButton}
              disabled={deleteMutation.isPending}
              onClick={() => deleteMutation.mutate()}
            >
              {deleteMutation.isPending ? "Deleting…" : "Delete for good"}
            </button>
            <button
              type="button"
              className={secondaryButton}
              disabled={deleteMutation.isPending}
              onClick={() => setIsConfirmingDelete(false)}
            >
              Keep it
            </button>
          </div>
        </div>
      ) : null}
      {failed ? (
        <p role="alert" className="m-0 text-caption text-danger">
          That didn’t work. Reload the page and try again.
        </p>
      ) : null}
    </div>
  );
}
