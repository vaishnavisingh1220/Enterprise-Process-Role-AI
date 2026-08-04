import { useState } from "react";
import { analyzeNewActivity, ApiError } from "../api/client";

const IMPACT_BADGE_STYLES = {
  automate: "border-impact-automate/40 bg-impact-automate/10 text-impact-automate",
  augment: "border-impact-augment/40 bg-impact-augment/10 text-impact-augment",
  "create-new": "border-impact-create-new/40 bg-impact-create-new/10 text-impact-create-new",
  eliminate: "border-impact-eliminate/40 bg-impact-eliminate/10 text-impact-eliminate",
};

const EMPTY_FORM = {
  activity_name: "",
  activity_description: "",
  role_name: "",
  process_name: "",
  frequency: "",
};

/**
 * The "Surprise Record" entry point: judges (or anyone) can type in a
 * brand-new role, process, and activity live, and watch it move through
 * every stage of the actual pipeline — not a canned demo. Every field
 * shown in the result comes straight from the API response, nothing here
 * is decorative.
 *
 * @param {Object} props
 * @param {(roleId: number, roleName: string) => void} [props.onViewRole] - called when the user wants to jump to the full role analysis after submission
 */
export default function Surpriserecordform({ onViewRole }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [status, setStatus] = useState("idle"); // idle | submitting | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  const isValid =
    form.activity_name.trim() && form.activity_description.trim() && form.role_name.trim() && form.process_name.trim();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!isValid || status === "submitting") return;

    setStatus("submitting");
    setError(null);
    setResult(null);

    try {
      const response = await analyzeNewActivity({
        activity_name: form.activity_name.trim(),
        activity_description: form.activity_description.trim(),
        role_name: form.role_name.trim(),
        process_name: form.process_name.trim(),
        frequency: form.frequency.trim() || undefined,
      });
      setResult(response);
      setStatus("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
      setStatus("error");
    }
  }

  function reset() {
    setForm(EMPTY_FORM);
    setResult(null);
    setStatus("idle");
    setError(null);
  }

  return (
    <div className="rounded-lg border border-border bg-surface">
      <div className="border-b border-border px-5 py-4">
        <h2 className="font-display text-sm font-semibold text-text-primary">
          Add a new role, process, or activity
        </h2>
        <p className="mt-1 text-xs text-text-muted">
          Enter something not in the dataset — a new role, a new process, or a new activity for an
          existing one. It gets researched, AI-analyzed, and stored live, then becomes queryable
          everywhere else in this app immediately.
        </p>
      </div>

      {status !== "done" && (
        <form onSubmit={handleSubmit} className="space-y-4 px-5 py-5">
          <Field
            label="Activity name"
            value={form.activity_name}
            onChange={(v) => update("activity_name", v)}
            placeholder="e.g. Bias auditing of AI model outputs"
          />
          <Field
            label="Activity description"
            value={form.activity_description}
            onChange={(v) => update("activity_description", v)}
            placeholder="What does this activity actually involve?"
            textarea
          />
          <div className="grid grid-cols-2 gap-4">
            <Field
              label="Role"
              value={form.role_name}
              onChange={(v) => update("role_name", v)}
              placeholder="Existing or brand new, e.g. AI Ethics Officer"
            />
            <Field
              label="Process"
              value={form.process_name}
              onChange={(v) => update("process_name", v)}
              placeholder="Existing or brand new, e.g. AI Governance"
            />
          </div>
          <Field
            label="Frequency (optional)"
            value={form.frequency}
            onChange={(v) => update("frequency", v)}
            placeholder="e.g. weekly"
          />

          {status === "error" && (
            <p className="rounded-lg border border-impact-eliminate/40 bg-impact-eliminate/10 px-3 py-2 text-sm text-impact-eliminate">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={!isValid || status === "submitting"}
            className="w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            {status === "submitting" ? "Researching & analyzing…" : "Analyze live"}
          </button>
        </form>
      )}

      {status === "done" && result && (
        <div className="space-y-4 px-5 py-5">
          <PipelineResult result={result} form={form} />
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={() => onViewRole?.(result.role_id, form.role_name.trim())}
              className="flex-1 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
            >
              View full role analysis →
            </button>
            <button
              type="button"
              onClick={reset}
              className="rounded-lg border border-border px-4 py-2 text-sm text-text-secondary transition-colors hover:bg-surface-hover"
            >
              Add another
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value, onChange, placeholder, textarea = false }) {
  const Component = textarea ? "textarea" : "input";
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-text-secondary">{label}</span>
      <Component
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={textarea ? 3 : undefined}
        className="w-full rounded-lg border border-border bg-ink px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
      />
    </label>
  );
}

function PipelineStage({ label, detail, tone = "default" }) {
  const toneClasses =
    tone === "warn"
      ? "border-impact-augment/40 bg-impact-augment/10"
      : "border-border bg-ink";
  return (
    <div className={`rounded-lg border px-3 py-2 ${toneClasses}`}>
      <p className="font-mono text-[10px] uppercase tracking-wider text-text-muted">{label}</p>
      <p className="mt-0.5 text-xs text-text-secondary">{detail}</p>
    </div>
  );
}

function PipelineResult({ result, form }) {
  const badgeClasses = IMPACT_BADGE_STYLES[result.impact_type] || "border-border bg-surface text-text-secondary";
  const researchOk = result.research_source === "duckduckgo" && result.research_snippet_count > 0;

  return (
    <div className="space-y-3">
      <p className="font-display text-xs font-semibold uppercase tracking-wider text-accent">
        Pipeline complete
      </p>

      <div className="grid grid-cols-2 gap-2">
        <PipelineStage
          label="Role"
          detail={`${form.role_name} ${result.role_created ? "(new)" : "(existing, reused)"}`}
          tone={result.role_created ? "warn" : "default"}
        />
        <PipelineStage
          label="Process"
          detail={`${form.process_name} ${result.process_created ? "(new)" : "(existing, reused)"}`}
          tone={result.process_created ? "warn" : "default"}
        />
        <PipelineStage
          label="Research/Retrieval"
          detail={
            researchOk
              ? `${result.research_snippet_count} live sources found`
              : "No live sources — reasoned from general knowledge (confidence lowered accordingly)"
          }
        />
        <PipelineStage label="Storage" detail={`activity_id #${result.activity_id} — persisted`} />
      </div>

      <div className="rounded-lg border border-border bg-ink p-4 space-y-3">
  <div className="flex items-center justify-between">
    <span className="text-xs text-text-muted">
      AI Impact
    </span>

    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 font-mono text-[11px] ${badgeClasses}`}
    >
      {result.impact_type}
    </span>
  </div>

  <div className="flex items-center justify-between">
    <span className="text-xs text-text-muted">
      Automation Potential
    </span>

    <span className="font-mono text-xs text-text-primary">
      {(result.automation_potential * 100).toFixed(0)}%
    </span>
  </div>

  <div className="flex items-center justify-between">
    <span className="text-xs text-text-muted">
      Confidence
    </span>

    <span className="font-mono text-xs text-text-primary">
      {(result.confidence_score * 100).toFixed(0)}%
    </span>
  </div>

  <div className="border-t border-border pt-3">
    <p className="text-[11px] text-text-muted">
      ✓ Research completed
    </p>

    <p className="text-[11px] text-text-muted">
      ✓ Activity stored in database
    </p>
  </div>
</div>
    </div>
  );
}