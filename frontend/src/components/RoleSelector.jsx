import { useEffect, useState } from "react";
import { getRoles, ApiError } from "../api/client";

/**
 * Fetches all roles and renders them as a custom listbox, grouped by
 * department. Calls onSelect(role) with the full RoleSummary object when
 * the user picks one.
 *
 * @param {Object} props
 * @param {(role: import("../api/client").RoleSummary) => void} props.onSelect
 * @param {?number} props.selectedRoleId
 */
export default function RoleSelector({ onSelect, selectedRoleId = null }) {
  const [roles, setRoles] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    getRoles()
      .then((data) => {
        if (cancelled) return;
        setRoles(data);
        setStatus("ready");
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Something went wrong loading roles.");
        setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return (
      <div className="space-y-2" aria-busy="true" aria-label="Loading roles">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-11 rounded-lg bg-surface animate-pulse"
            style={{ animationDelay: `${i * 60}ms` }}
          />
        ))}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="rounded-lg border border-impact-eliminate/40 bg-impact-eliminate/10 p-4">
        <p className="font-display text-sm font-semibold text-impact-eliminate">
          Couldn't load roles
        </p>
        <p className="mt-1 text-sm text-text-secondary">{error}</p>
      </div>
    );
  }

  // Group by department so related roles (e.g. Procurement) sit together
  const grouped = roles.reduce((acc, role) => {
    const key = role.department || "Other";
    (acc[key] ||= []).push(role);
    return acc;
  }, {});

  return (
    <nav aria-label="Select a role" className="space-y-5">
      {Object.entries(grouped).map(([department, deptRoles]) => (
        <div key={department}>
          <h3 className="mb-2 font-display text-xs font-semibold uppercase tracking-wider text-text-muted">
            {department}
          </h3>
          <ul className="space-y-1">
            {deptRoles.map((role) => {
              const isSelected = role.role_id === selectedRoleId;
              return (
                <li key={role.role_id}>
                  <button
                    type="button"
                    onClick={() => onSelect(role)}
                    aria-current={isSelected ? "true" : undefined}
                    className={`group flex w-full items-center justify-between rounded-lg border px-3 py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                      isSelected
                        ? "border-accent/50 bg-accent/10"
                        : "border-transparent bg-surface hover:bg-surface-hover"
                    }`}
                  >
                    <span
                      className={`text-sm font-medium ${
                        isSelected ? "text-text-primary" : "text-text-secondary group-hover:text-text-primary"
                      }`}
                    >
                      {role.name}
                    </span>
                    {role.seniority_level && (
                      <span className="font-mono text-[11px] text-text-muted">
                        {role.seniority_level}
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}