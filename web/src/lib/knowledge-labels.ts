import type { KnowledgeFileType, KnowledgeStatus } from "@/lib/api-client";

/** How each kind of Knowledge file is named on screen. */
export const knowledgeFileTypeLabels: Record<KnowledgeFileType, string> = {
  text: "Text",
  markdown: "Markdown",
  pdf: "PDF",
};

/** Each Knowledge status, its label and its pill's colours. */
export const knowledgeStatuses: {
  status: KnowledgeStatus;
  label: string;
  pill: string;
}[] = [
  { status: "ready", label: "Ready", pill: "bg-blue-tint text-blue-deep" },
  {
    status: "pending",
    label: "Pending",
    pill: "bg-yellow-tint text-yellow-deep",
  },
  {
    status: "failed",
    label: "Failed",
    pill: "bg-danger-tint text-danger-deep",
  },
];
