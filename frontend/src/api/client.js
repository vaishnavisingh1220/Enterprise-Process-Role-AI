/**
 * API client for the Process-to-Role Intelligence backend.
 *
 * Every function's return shape matches backend/api/schemas.py EXACTLY —
 * field names are not guessed. If you're building a new component and
 * need a shape not covered by a JSDoc typedef below, check schemas.py
 * first rather than inferring from a sample response.
 *
 * Set VITE_API_BASE_URL in frontend/.env to point elsewhere (defaults to
 * the local FastAPI dev server).
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Typedefs (mirror api/schemas.py — keep in sync if the backend schema changes)
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} RoleSummary
 * @property {number} role_id
 * @property {string} name
 * @property {?string} department
 * @property {?string} seniority_level
 */

/**
 * @typedef {Object} AIImpact
 * @property {string} impact_type - "automate" | "augment" | "eliminate" | "create-new"
 * @property {number} automation_potential - 0.0-1.0
 * @property {number} confidence_score - 0.0-1.0
 * @property {string} rationale
 * @property {string} evidence_source
 */

/**
 * @typedef {Object} ActivityEvidence
 * @property {number} activity_id
 * @property {string} activity_name
 * @property {number} process_id
 * @property {string} process_name
 * @property {?string} involvement_level
 * @property {?string} frequency
 * @property {?AIImpact} ai_impact
 * @property {?string} future_responsibility
 */

/**
 * @typedef {Object} RoleEvidenceBundle
 * @property {number} role_id
 * @property {string} role_name
 * @property {?string} department
 * @property {?string} seniority_level
 * @property {string[]} processes_involved
 * @property {number} activity_count
 * @property {Object.<string, number>} impact_summary - e.g. { automate: 3, augment: 4 }
 * @property {ActivityEvidence[]} activities
 */

/**
 * @typedef {Object} RoleAnalysisResponse
 * @property {number} analysis_id
 * @property {number} role_id
 * @property {string} role_name
 * @property {string} narrative
 * @property {RoleEvidenceBundle} evidence
 * @property {string} created_at
 */

/**
 * @typedef {Object} MultiProcessRole
 * @property {number} role_id
 * @property {string} role_name
 * @property {number} process_count
 * @property {string[]} processes
 * @property {number} activity_count
 */

/**
 * @typedef {Object} ProcessSummary
 * @property {number} process_id
 * @property {string} name
 * @property {?string} description
 */

/**
 * @typedef {Object} ProcessActivitySummary
 * @property {number} activity_id
 * @property {string} activity_name
 * @property {string[]} roles
 * @property {?string} impact_type
 * @property {?number} automation_potential
 */

/**
 * @typedef {Object} ProcessDetail
 * @property {number} process_id
 * @property {string} name
 * @property {?string} description
 * @property {string[]} roles_involved
 * @property {ProcessActivitySummary[]} activities
 */

/**
 * @typedef {Object} ActivityImpactSummary
 * @property {number} activity_id
 * @property {string} activity_name
 * @property {string} process_name
 * @property {string[]} roles
 * @property {number} automation_potential
 * @property {number} confidence_score
 */

/**
 * @typedef {Object} AnalysisHistoryItem
 * @property {number} analysis_id
 * @property {string} query_type
 * @property {number} target_id
 * @property {string} created_at
 */

/**
 * @typedef {Object} AnalysisHistoryDetail
 * @property {number} analysis_id
 * @property {string} query_type
 * @property {number} target_id
 * @property {Object} evidence
 * @property {string} narrative
 * @property {string} created_at
 */

// ---------------------------------------------------------------------------
// Request helper
// ---------------------------------------------------------------------------

class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request(path) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`);
  } catch (networkErr) {
    // Backend unreachable entirely (not running, wrong port, CORS block, etc.)
    throw new ApiError(
      `Could not reach the backend at ${BASE_URL}. Is uvicorn running?`,
      0,
      networkErr.message
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = body.detail || "";
    } catch {
      /* response wasn't JSON, ignore */
    }
    throw new ApiError(
      `Request to ${path} failed (${response.status})`,
      response.status,
      detail
    );
  }

  return response.json();
}

async function postRequest(path, body) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (networkErr) {
    throw new ApiError(
      `Could not reach the backend at ${BASE_URL}. Is uvicorn running?`,
      0,
      networkErr.message
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const respBody = await response.json();
      detail = respBody.detail || "";
    } catch {
      /* response wasn't JSON, ignore */
    }
    throw new ApiError(`Request to ${path} failed (${response.status})`, response.status, detail);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Roles
// ---------------------------------------------------------------------------

/** @returns {Promise<RoleSummary[]>} */
export function getRoles() {
  return request("/roles");
}

/** @returns {Promise<MultiProcessRole[]>} */
export function getMultiProcessRoles() {
  return request("/roles/multi-process");
}

/** @param {number} roleId @returns {Promise<RoleEvidenceBundle>} */
export function getRole(roleId) {
  return request(`/roles/${roleId}`);
}

/**
 * Full pipeline: reasoning engine -> LLM synthesis -> persisted trace.
 * This is the "Show me how AI could affect a Procurement Manager" call.
 * Can be slow (LLM call) — always show a loading state when calling this.
 * @param {number} roleId @returns {Promise<RoleAnalysisResponse>}
 */
export function getRoleAnalysis(roleId) {
  return request(`/roles/${roleId}/analysis`);
}

// ---------------------------------------------------------------------------
// Processes
// ---------------------------------------------------------------------------

/** @returns {Promise<ProcessSummary[]>} */
export function getProcesses() {
  return request("/processes");
}

/** @param {number} processId @returns {Promise<ProcessDetail>} */
export function getProcess(processId) {
  return request(`/processes/${processId}`);
}

/**
 * @param {"automate"|"augment"|"eliminate"|"create-new"} impactType
 * @returns {Promise<ActivityImpactSummary[]>}
 */
export function getActivitiesByImpact(impactType) {
  return request(`/processes/impact/${impactType}`);
}

// ---------------------------------------------------------------------------
// Analysis history
// ---------------------------------------------------------------------------

/** @param {number} [limit=50] @returns {Promise<AnalysisHistoryItem[]>} */
export function getAnalysisHistory(limit = 50) {
  return request(`/analysis/history?limit=${limit}`);
}

/** @param {number} analysisId @returns {Promise<AnalysisHistoryDetail>} */
export function getAnalysisHistoryDetail(analysisId) {
  return request(`/analysis/history/${analysisId}`);
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} ChatResponse
 * @property {number} analysis_id
 * @property {string} question
 * @property {string} matched_intent
 * @property {string[]} matched_roles
 * @property {string[]} matched_processes
 * @property {string} answer
 * @property {Object} evidence
 * @property {string} created_at
 */

/**
 * Free-text Q&A, grounded in the same reasoning engine every other
 * endpoint uses. Can be slow (LLM call) — always show a loading state.
 * @param {string} message @returns {Promise<ChatResponse>}
 */
export function askChat(message) {
  return postRequest("/chat/ask", { message });
}

// ---------------------------------------------------------------------------
// Dynamic intake — the "Surprise Record" pipeline
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} DynamicActivityResponse
 * @property {number} activity_id
 * @property {number} role_id
 * @property {boolean} role_created
 * @property {number} process_id
 * @property {boolean} process_created
 * @property {string} impact_type
 * @property {number} automation_potential
 * @property {number} confidence_score
 * @property {string} rationale
 * @property {string} evidence_source
 * @property {string} future_responsibility
 * @property {string} research_source - "duckduckgo" | "unavailable"
 * @property {number} research_snippet_count
 * @property {boolean} parse_failed
 */

/**
 * Submits a brand-new activity (with a role and/or process that may also
 * be brand new) for live research + AI analysis + persistence. After this
 * resolves, the new record is immediately queryable via getRole(role_id)
 * or askChat() — nothing else needs to happen for it to be "real" data.
 * @param {{activity_name: string, activity_description: string, role_name: string, process_name: string, frequency?: string}} payload
 * @returns {Promise<DynamicActivityResponse>}
 */
export function analyzeNewActivity(payload) {
  return postRequest("/dynamic/analyze-activity", payload);
}

export { ApiError };