import { AdminPageHeader } from "@/components/AdminPageHeader";
import { EvalAreaTabs } from "@/components/EvalAreaTabs";
import { JudgeSettingsEditor } from "@/components/JudgeSettingsEditor";

/**
 * The admin page for the Judge's model, thinking and prompts.
 *
 * @returns The page.
 */
export default function AdminEvalJudgePage() {
  return (
    <div className="flex flex-col gap-[22px]">
      <AdminPageHeader
        title="Judge"
        lead="The model that marks Persona, Knowledge and Understanding cases. Changes apply from the next run; each run keeps the Judge it used."
      />
      <EvalAreaTabs />
      <JudgeSettingsEditor />
    </div>
  );
}
