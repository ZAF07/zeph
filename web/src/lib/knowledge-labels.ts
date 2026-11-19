import type { KnowledgeFileType, KnowledgeStatus } from "@/lib/api-client";

/** The traditions an Admin can file a Knowledge document under. */
export const knowledgeTraditions = [
  "Stoicism",
  "Buddhism",
  "Taoism",
  "Existentialism",
  "Psychology",
  "Mindfulness",
  "Other",
];

/** How each kind of Knowledge file is named on screen. */
export const knowledgeFileTypeLabels: Record<KnowledgeFileType, string> = {
  text: "Text",
  markdown: "Markdown",
  pdf: "PDF",
};

/**
 * Each Knowledge status's label and tag tone, in the order counted: orange
 * while indexing, danger when it failed.
 */
export const knowledgeStatusLabels: Record<
  KnowledgeStatus,
  { label: string; tone: "plain" | "orange" | "danger" }
> = {
  ready: { label: "Ready", tone: "plain" },
  pending: { label: "Pending", tone: "orange" },
  failed: { label: "Failed", tone: "danger" },
};

/** Every Knowledge status, in the order counted. */
export const knowledgeStatusOrder: KnowledgeStatus[] = [
  "ready",
  "pending",
  "failed",
];
