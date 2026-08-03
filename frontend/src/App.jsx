import { useEffect, useState } from "react";
import RoleSelector from "./components/RoleSelector";
import { getRole, getRoleAnalysis, ApiError } from "./api/client";

const IMPACT_LABELS = {
  automate: "Automate",
  augment: "Augment",
  "create-new": "New responsibility",
  eliminate: "Eliminate",
};

/** Static class maps per impact_type — Tailwind can't detect dynamically
 * interpolated class names (e.g. `text-${color}`) at build time, so every
 * combination must appear as a literal string somewhere in source. */
const IMPACT_BADGE_STYLES = {
  automate: "border-impact-automate/40 bg-impact-automate/10 text-impact-automate",
  augment: "border-impact-augment/40 bg-impact-augment/10 text-impact-augment",
  "create-new": "border-impact-create-new/40 bg-impact-create-new/10 text-impact-create-new",
  eliminate: "border-impact-eliminate/40 bg-impact-eliminate/10 text-impact-eliminate",
};

function ImpactBadge({ type }) {
  const classes = IMPACT_BADGE_STYLES[type] || "border-border bg-surface text-text-secondary";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[11px] font-medium ${classes}`}
    >
      {IMPACT_LABELS[type] || type}
    </span>
  );
}

function ImpactSummaryLegend({ summary }) {
  const entries = Object.entries(summary);
  if (entries.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([type, count]) => (
        <span key={type} className="flex items-center gap-1.5">
          <ImpactBadge type={type} />
          <span className="font-mono text-xs text-text-muted">×{count}</span>
        </span>
      ))}
    </div>
  );
}

function ActivityRow({ activity }) {
  const impact = activity.ai_impact;
  return (
    <li className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-text-primary">{activity.activity_name}</p>
          <p className="mt-0.5 text-xs text-text-muted">
            {activity.process_name}
            {activity.involvement_level && ` · ${activity.involvement_level}`}
          </p>
        </div>
        <span className="shrink-0 font-mono text-[11px] text-text-muted">
          #{activity.activity_id}
        </span>
      </div>

      {impact && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <ImpactBadge type={impact.impact_type} />
          <span className="font-mono text-[11px] text-text-muted">
            confidence {impact.confidence_score.toFixed(2)}
          </span>
        </div>
      )}

      {impact?.rationale && (
        <p className="mt-2 text-xs leading-relaxed text-text-secondary">{impact.rationale}</p>
      )}

      {activity.future_responsibility && (
        <p className="mt-2 border-t border-border pt-2 text-xs leading-relaxed text-text-secondary">
          <span className="font-medium text-text-primary">Future: </span>
          {activity.future_responsibility}
        </p>
      )}
    </li>
  );
}

export default function App() {
  const [selectedRole, setSelectedRole] = useState(null);

  const [detail, setDetail] = useState(null);
  const [detailStatus, setDetailStatus] = useState("idle"); // idle | loading | ready | error
  const [detailError, setDetailError] = useState(null);

  const [analysis, setAnalysis] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState("idle"); // idle | loading | ready | error
  const [analysisError, setAnalysisError] = useState(null);

  // Fetch the reasoning-engine evidence bundle immediately on role selection.
  // No LLM involved here — this is the "prove it works without AI" view.
  useEffect(() => {
    if (!selectedRole) return;

    let cancelled = false;
    setDetail(null);
    setAnalysis(null);
    setAnalysisStatus("idle");
    setDetailStatus("loading");

    getRole(selectedRole.role_id)
      .then((data) => {
        if (cancelled) return;
        setDetail(data);
        setDetailStatus("ready");
      })
      .catch((err) => {
        if (cancelled) return;
        setDetailError(err instanceof ApiError ? err.message : "Failed to load role detail.");
        setDetailStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRole]);

  function runAnalysis() {
    if (!selectedRole) return;
    setAnalysisStatus("loading");
    setAnalysisError(null);

    getRoleAnalysis(selectedRole.role_id)
      .then((data) => {
        setAnalysis(data);
        setAnalysisStatus("ready");
      })
      .catch((err) => {
        setAnalysisError(
          err instanceof ApiError ? err.message : "Failed to run AI analysis."
        );
        setAnalysisStatus("error");
      });
  }

  return (
    <div className="min-h-screen bg-ink">
      <header className="border-b border-border px-8 py-5">
        <h1 className="font-display text-xl font-bold text-text-primary">
          Process-to-Role Intelligence
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Select a role to see how AI affects the activities it performs.
        </p>
      </header>

      <div className="flex gap-8 p-8">
        <aside className="w-64 shrink-0">
          <RoleSelector onSelect={setSelectedRole} selectedRoleId={selectedRole?.role_id} />
        </aside>

        <main className="min-w-0 flex-1">
          {!selectedRole && (
            <div className="rounded-lg border border-dashed border-border p-12 text-center">
              <p className="text-sm text-text-secondary">
                Pick a role on the left to see its activities and AI impact.
              </p>
            </div>
          )}

          {selectedRole && detailStatus === "loading" && (
            <div className="space-y-3" aria-busy="true">
              <div className="h-20 rounded-lg bg-surface animate-pulse" />
              <div className="h-20 rounded-lg bg-surface animate-pulse" />
              <div className="h-20 rounded-lg bg-surface animate-pulse" />
            </div>
          )}

          {selectedRole && detailStatus === "error" && (
            <div className="rounded-lg border border-impact-eliminate/40 bg-impact-eliminate/10 p-4">
              <p className="font-display text-sm font-semibold text-impact-eliminate">
                Couldn't load this role
              </p>
              <p className="mt-1 text-sm text-text-secondary">{detailError}</p>
            </div>
          )}

          {selectedRole && detailStatus === "ready" && detail && (
            <div className="space-y-6">
              <div>
                <h2 className="font-display text-lg font-bold text-text-primary">
                  {detail.role_name}
                </h2>
                <p className="mt-1 text-sm text-text-secondary">
                  {detail.department} · involved in {detail.processes_involved.length} process
                  {detail.processes_involved.length !== 1 && "es"}:{" "}
                  {detail.processes_involved.join(", ")}
                </p>
                <div className="mt-3">
                  <ImpactSummaryLegend summary={detail.impact_summary} />
                </div>
              </div>

              <div>
                <button
                  type="button"
                  onClick={runAnalysis}
                  disabled={analysisStatus === "loading"}
                  className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {analysisStatus === "loading" ? "Running AI analysis…" : "Run AI analysis"}
                </button>

                {analysisStatus === "error" && (
                  <p className="mt-2 text-sm text-impact-eliminate">{analysisError}</p>
                )}

                {analysisStatus === "ready" && analysis && (
                  <div className="mt-4 rounded-lg border border-accent/30 bg-accent/5 p-4">
                    <p className="mb-2 font-display text-xs font-semibold uppercase tracking-wider text-accent">
                      AI narrative · analysis #{analysis.analysis_id}
                    </p>
                    <p className="whitespace-pre-line text-sm leading-relaxed text-text-primary">
                      {analysis.narrative}
                    </p>
                  </div>
                )}
              </div>

              <div>
                <h3 className="mb-3 font-display text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Activities ({detail.activities.length})
                </h3>
                <ul className="space-y-3">
                  {detail.activities.map((activity) => (
                    <ActivityRow key={activity.activity_id} activity={activity} />
                  ))}
                </ul>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}