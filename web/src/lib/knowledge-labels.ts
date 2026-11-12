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

/** Each Knowledge status's label and pill colours, in the order counted. */
export const knowledgeStatusLabels: Record<
  KnowledgeStatus,
  { label: string; pill: string }
> = {
  ready: { label: "Ready", pill: "bg-blue-tint text-blue-deep" },
  pending: { label: "Pending", pill: "bg-yellow-tint text-yellow-deep" },
  failed: { label: "Failed", pill: "bg-danger-tint text-danger-deep" },
};

/** Every Knowledge status, in the order counted. */
export const knowledgeStatusOrder: KnowledgeStatus[] = [
  "ready",
  "pending",
  "failed",
];
