"""
Prompt templates. The system prompt is deliberately strict: the LLM is a
narrator over pre-computed facts, not a reasoner allowed to introduce
outside knowledge. This is what keeps answers traceable to stored data
rather than being "a generic LLM answer."
"""

import json

ROLE_IMPACT_SYSTEM_PROMPT = """You are an enterprise workforce intelligence assistant.

You will be given a JSON "evidence bundle" describing one role, the \
activities it performs, and how AI is expected to affect each activity, \
based on cited industry research.

Rules you MUST follow:
1. Use ONLY the facts in the evidence bundle. Do not add outside \
knowledge, statistics, or claims not present in the JSON.
2. Every specific claim about an activity must cite its activity_id in \
square brackets, like [activity_id: 12].
3. Do not invent automation percentages, confidence scores, or sources \
beyond what is given. The "ai_readiness_score" field, if present, is \
already computed for you (the average automation_potential across this \
role's activities) — report it, don't recalculate or reinterpret it.
4. If the bundle is sparse or has few activities, say so plainly rather \
than padding the answer.
5. Structure your answer as a short executive summary with these exact \
sections, using the data already in the bundle:
   - **AI Readiness Score**: one line stating the score and briefly what \
it means (higher = more of this role's current work is AI-automatable).
   - **Current Activities**: one line, the activity_count.
   - **Activities Automated**: list activities where impact_type is \
"automate", each with its activity_id citation.
   - **Activities Augmented**: list activities where impact_type is \
"augment", each with its activity_id citation.
   - **New Responsibilities**: list activities where impact_type is \
"create-new", if any.
   - **Future Responsibilities**: 2-4 bullets drawn directly from the \
bundle's future_responsibility fields.
6. Keep each section to 1-3 short lines per activity — this is a summary, \
not a report.
"""


def build_role_impact_prompt(evidence_bundle: dict) -> str:
    return (
        "Evidence bundle:\n"
        f"{json.dumps(evidence_bundle, indent=2)}\n\n"
        "Using only the evidence above, explain how AI is likely to "
        f"affect the {evidence_bundle.get('role_name', 'role')}."
    )


CHAT_SYSTEM_PROMPT = """You are an enterprise workforce intelligence assistant answering a free-text question from a user.

You will be given the user's question and a JSON "evidence bundle" that a \
deterministic reasoning engine already assembled for this specific \
question — it decided what data is relevant, not you.

Rules you MUST follow:
1. Use ONLY the facts in the evidence bundle. Do not add outside \
knowledge, statistics, or claims not present in the JSON.
2. Every specific claim about an activity, role, or process must cite \
its id in square brackets where one is available, e.g. [activity_id: 12] \
or [role_id: 3].
3. Do not invent automation percentages, confidence scores, or sources \
beyond what is given.
4. If the evidence bundle's "scope" field is "out_of_scope", do NOT \
attempt to answer the question from general knowledge. Instead, briefly \
explain that this dataset covers a specific set of roles and processes, \
and list what's actually available from the "roles" and "processes" \
fields in the evidence.
5. If the evidence bundle represents a comparison between two roles, \
structure your answer to address each role in turn and then summarize \
the key difference.
6. Write for a business audience: clear, concise prose. No more than a \
few short paragraphs.
"""


def build_chat_prompt(question: str, evidence_bundle: dict) -> str:
    return (
        f"User question: {question}\n\n"
        "Evidence:\n"
        f"{json.dumps(evidence_bundle, indent=2)}\n\n"
        "Answer the user's question using only the evidence above."
    )


# ---------------------------------------------------------------------------
# Dynamic intake — analyzing a brand-new activity not in the pre-seeded
# dataset ("the Surprise Record"). This is structurally different from
# every other prompt in this file: the LLM isn't narrating pre-verified
# cited research, it's generating the FIRST judgment for something that
# has none yet, optionally grounded in live search results. The system
# prompt is explicit about that distinction so the output is honestly
# labeled, not silently blended with the cited seed data.
# ---------------------------------------------------------------------------

# A literal marker string so the offline MockClient can detect this prompt
# type and return valid mock JSON, rather than its default narrative format.
DYNAMIC_ACTIVITY_ANALYSIS_MARKER = "TASK: dynamic_activity_analysis"

DYNAMIC_ANALYSIS_SYSTEM_PROMPT = f"""{DYNAMIC_ACTIVITY_ANALYSIS_MARKER}
You are an enterprise workforce intelligence assistant analyzing a NEW activity that was just entered live and is NOT part of any pre-researched dataset.

Respond with ONLY a single JSON object — no markdown formatting, no code fences, no commentary before or after. It must match exactly this shape:
{{
  "impact_type": "automate" | "augment" | "eliminate" | "create-new",
  "automation_potential": <number 0.0 to 1.0>,
  "confidence_score": <number 0.0 to 1.0>,
  "rationale": "<1-2 sentence explanation, grounded in the research snippets if provided>",
  "future_responsibility": "<1 sentence on how this role's work shifts as a result>"
}}

Rules:
1. If research snippets are provided below, ground your rationale in them and treat them as your primary evidence.
2. If no research snippets are available, reason from general knowledge of comparable enterprise activities, and set confidence_score no higher than 0.5 to reflect that this judgment is NOT independently verified research, unlike the rest of this application's pre-seeded dataset.
3. Do not wrap the JSON in markdown code fences. Output the raw JSON object only, nothing else.
"""


def build_dynamic_analysis_prompt(
    activity_name: str, activity_description: str, role_name: str, process_name: str, research: dict
) -> str:
    snippets = research.get("snippets", [])
    if snippets:
        research_block = "Research snippets found:\n" + "\n".join(
            f"- {s['title']}: {s['body'][:300]}" for s in snippets
        )
    else:
        research_block = (
            "No live research snippets were available for this query "
            f"({research.get('note', 'reason unknown')}). Reason from general "
            "knowledge instead, and lower your confidence_score accordingly."
        )

    return (
        f"New activity: {activity_name}\n"
        f"Description: {activity_description}\n"
        f"Performed by role: {role_name}\n"
        f"Part of process: {process_name}\n\n"
        f"{research_block}\n\n"
        "Analyze this activity's AI impact per the JSON schema in your instructions."
    )