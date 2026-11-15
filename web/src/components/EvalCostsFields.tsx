"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import { ApiError, type EvalCosts } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

type PriceRow = { model: string; sgdIn: string; sgdOut: string };

/**
 * Reads a price typed into a field.
 *
 * @param typed - What was typed.
 * @returns The number, or null when the field is empty.
 */
function readPrice(typed: string): number | null {
  return typed.trim() === "" ? null : Number(typed);
}

/**
 * The Model Prices and token limit fields, filled with what is saved now,
 * and the Save button.
 *
 * @param props - `costs` is what is saved now.
 * @returns The form.
 */
export function EvalCostsFields({ costs }: { costs: EvalCosts }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [rows, setRows] = useState<PriceRow[]>(
    costs.prices.map((price) => ({
      model: price.model,
      sgdIn: price.sgd_in === null ? "" : String(price.sgd_in),
      sgdOut: price.sgd_out === null ? "" : String(price.sgd_out),
    })),
  );
  const [tokenLimit, setTokenLimit] = useState(String(costs.token_limit));
  const saveMutation = useMutation({
    mutationFn: (changed: EvalCosts) => apiClient.saveEvalCosts(changed),
    onSuccess: (saved) => {
      queryClient.setQueryData(queryKeys.evalCosts, saved);
    },
  });
  const savedModels = new Set(costs.prices.map((price) => price.model));

  function changeRow(index: number, change: Partial<PriceRow>) {
    setRows(
      rows.map((row, rowIndex) =>
        rowIndex === index ? { ...row, ...change } : row,
      ),
    );
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveMutation.mutate({
      prices: rows
        .filter((row) => row.model.trim() !== "")
        .map((row) => ({
          model: row.model.trim(),
          sgd_in: readPrice(row.sgdIn),
          sgd_out: readPrice(row.sgdOut),
        })),
      token_limit: Number(tokenLimit),
    });
  }

  const error = saveMutation.error;

  return (
    <form onSubmit={save} className="flex flex-col gap-6">
      <section className="flex flex-col gap-3">
        <h2 className="m-0 text-[17px] font-semibold">Model Prices</h2>
        <p className={fieldCaption}>
          SGD per 1,000,000 tokens the model reads (in) and writes (out). Use
          DeepSeek’s peak, cache-miss price so estimates are never too low.
          Leave both empty for no price: that model’s tokens show without a
          cost, marked “no price set”, and never stop a run. A run keeps the
          prices it started with.
        </p>
        <div className="overflow-x-auto rounded-xl border border-line bg-white">
          <table className="w-full min-w-[560px] border-collapse text-sm">
            <thead>
              <tr>
                {["Model", "SGD in per 1M", "SGD out per 1M"].map((heading) => (
                  <th
                    key={heading}
                    scope="col"
                    className="border-b border-line bg-subtle px-[18px] py-3 text-left font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr
                  key={index}
                  className="border-b border-line last:border-b-0"
                >
                  <td className="px-[18px] py-2.5">
                    {savedModels.has(row.model) ? (
                      <span className="font-mono">{row.model}</span>
                    ) : (
                      <input
                        aria-label="Model name"
                        className={inputField}
                        value={row.model}
                        onChange={(event) =>
                          changeRow(index, { model: event.target.value })
                        }
                      />
                    )}
                    {row.sgdIn === "" && row.sgdOut === "" ? (
                      <span className="ml-2 text-caption text-ink-muted">
                        no price set
                      </span>
                    ) : null}
                  </td>
                  <td className="px-[18px] py-2.5">
                    <input
                      aria-label={`${row.model || "New model"} SGD in`}
                      className={inputField}
                      inputMode="decimal"
                      value={row.sgdIn}
                      onChange={(event) =>
                        changeRow(index, { sgdIn: event.target.value })
                      }
                    />
                  </td>
                  <td className="px-[18px] py-2.5">
                    <input
                      aria-label={`${row.model || "New model"} SGD out`}
                      className={inputField}
                      inputMode="decimal"
                      value={row.sgdOut}
                      onChange={(event) =>
                        changeRow(index, { sgdOut: event.target.value })
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <button
            type="button"
            className={secondaryButton}
            onClick={() =>
              setRows([...rows, { model: "", sgdIn: "", sgdOut: "" }])
            }
          >
            Add a model
          </button>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="m-0 text-[17px] font-semibold">Eval run token limit</h2>
        <label className={`${fieldLabel} max-w-[320px]`}>
          Most tokens one run may use
          <input
            className={inputField}
            inputMode="numeric"
            value={tokenLimit}
            onChange={(event) => setTokenLimit(event.target.value)}
          />
        </label>
        <p className={fieldCaption}>
          Tokens in and out together. Once a run goes over this, it stops by
          itself as “Stopped over limit” after the case it is on, keeping every
          finished case. A whole run of every Eval uses about 430,000.
        </p>
      </section>

      {error ? (
        <p role="alert" className="m-0 text-caption text-danger">
          {error instanceof ApiError && error.detail
            ? error.detail
            : "Couldn’t save. Try again."}
        </p>
      ) : null}
      {saveMutation.isSuccess ? (
        <p role="status" className="m-0 text-caption text-ink-muted">
          Saved. New runs use these from now on.
        </p>
      ) : null}
      <div>
        <button
          type="submit"
          className={primaryButton}
          disabled={saveMutation.isPending}
        >
          {saveMutation.isPending ? "Saving…" : "Save"}
        </button>
      </div>
    </form>
  );
}
