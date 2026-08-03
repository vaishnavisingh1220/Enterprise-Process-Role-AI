"""
Seed data for the Process-to-Role Intelligence AI application.

Industry: Supply Chain & Procurement
Processes: Procurement (Source-to-Contract), Inventory Management,
           Warehouse Operations / Order Fulfillment

AI impact judgments (impact_type, automation_potential, rationale,
confidence_score) are derived from published 2025-2026 industry research
(Gartner, KPMG, MIT, Hackett Group, IBM, Oracle, Suplari, etc.) rather than
invented. Each activity's evidence_source cites where that judgment came
from, so every AI-generated recommendation the app produces can be traced
back to a real source via the activity -> ai_impact chain.

Run directly to build/reset the local SQLite database:
    python seed_data.py

Idempotent: if the industry already exists, seeding is skipped so re-running
the app (or restarting it) does not wipe or duplicate data.
"""

try:
    from database.models import get_engine, init_db, get_session, Industry, Process, Role, Activity, RoleActivity, AIImpact, FutureResponsibility
except ImportError:
    # running directly as `python seed_data.py` from inside database/
    from models import get_engine, init_db, get_session, Industry, Process, Role, Activity, RoleActivity, AIImpact, FutureResponsibility

# ---------------------------------------------------------------------------
# 1. Industry
# ---------------------------------------------------------------------------

INDUSTRY = {
    "name": "Supply Chain & Procurement",
    "description": (
        "Covers the source-to-contract procurement function, inventory "
        "management, and warehouse operations / order fulfillment for a "
        "mid-to-large enterprise with physical goods flowing from supplier "
        "to warehouse to customer."
    ),
    "source_notes": (
        "Researched from 2025-2026 industry reports including Gartner Supply "
        "Chain Practice, KPMG procurement automation estimates, The Hackett "
        "Group 2025 CPO Agenda, MIT Intelligent Logistics Systems Lab, IBM, "
        "Oracle SCM, and Suplari procurement role-impact analyses."
    ),
}

# ---------------------------------------------------------------------------
# 2. Processes
# ---------------------------------------------------------------------------

PROCESSES = [
    {
        "key": "A",
        "name": "Procurement (Source-to-Contract)",
        "description": (
            "The end-to-end process of identifying suppliers, sourcing "
            "goods/services, negotiating and contracting, and managing "
            "purchase orders and invoices."
        ),
    },
    {
        "key": "B",
        "name": "Inventory Management",
        "description": (
            "Forecasting demand, setting replenishment policy, tracking "
            "stock levels, and reconciling discrepancies across warehouse "
            "locations."
        ),
    },
    {
        "key": "C",
        "name": "Warehouse Operations / Order Fulfillment",
        "description": (
            "Physical execution of receiving, storing, picking, packing, "
            "and shipping goods, plus the labor, safety, and equipment "
            "management that supports it."
        ),
    },
]

# ---------------------------------------------------------------------------
# 3. Roles
# ---------------------------------------------------------------------------

ROLES = [
    {"name": "Procurement Manager", "department": "Procurement", "seniority_level": "Manager"},
    {"name": "Category Buyer", "department": "Procurement", "seniority_level": "Specialist"},
    {"name": "Procurement Analyst", "department": "Procurement", "seniority_level": "Analyst"},
    {"name": "Contract Manager", "department": "Procurement/Legal", "seniority_level": "Manager"},
    {"name": "Inventory Analyst", "department": "Supply Chain", "seniority_level": "Analyst"},
    {"name": "Warehouse Manager", "department": "Operations", "seniority_level": "Manager"},
    {"name": "Logistics Coordinator", "department": "Operations", "seniority_level": "Coordinator"},
    {"name": "Warehouse Associate", "department": "Operations", "seniority_level": "Associate"},
]

# ---------------------------------------------------------------------------
# 4. Activities (+ role links + AI impact + future responsibility)
#
# involvement_level: "primary" (does the work) / "secondary" (contributes)
#                     / "reviewer" (approves/oversees)
# impact_type: automate / augment / eliminate / create-new
# ---------------------------------------------------------------------------

SUPLARI_2035 = "Suplari (2025), \"10 Procurement Job Roles Most Impacted by AI (2025-2035)\" - https://suplari.com/10-procurement-job-roles-most-impacted-by-ai/"
SUPLARI_2036 = "Suplari (2026), \"10 Procurement Job Roles Most Impacted by AI (2026-2036)\" - https://suplari.com/blog/10-procurement-job-roles-most-impacted-by-ai"
SUPLARI_WORKDAY = "Suplari (2026), \"How to Augment your Procurement Team with AI\" - https://suplari.com/blog/how-to-augment-your-procurement-team-with-ai-the-9-hour-workday-is-about-to-become-1"
LIGHTSOURCE = "LightSource (2026), \"Every Job in Procurement and Supply Chain, Ranked by AI Risk\" - https://lightsource.ai/blog/every-procurement-supply-chain-job-ranked-by-ai-risk"
AOP_STATE = "Art of Procurement (2026), \"State of AI in Procurement 2026\" - https://artofprocurement.com/blog/state-of-ai-in-procurement"
AOP_AGENTS = "Art of Procurement (2026), \"AI Agents in Procurement\" - https://artofprocurement.com/blog/ai-agents-in-procurement"
HACKETT = "The Hackett Group (2025), \"64% of Procurement Leaders Say AI Will Transform Their Jobs\" - https://www.thehackettgroup.com/the-hackett-group-procurement-leaders-say-ai-will-transform-their-jobs/"
SCMR_GARTNER = "Supply Chain Management Review / Gartner (2026), \"AI is automating procurement; it's also creating jobs\" - https://www.scmr.com/article/ai-is-automating-procurement-its-also-creating-jobs-leaders-arent-ready-for"
ORACLE_WMS = "Oracle SCM (2025), \"AI in Warehouse Management: Impacts and Use Cases\" - https://www.oracle.com/scm/ai-warehouse-management/"
MECALUX = "Mecalux (2026), \"AI in warehouse management: impact and applications\" - https://www.mecalux.com/blog/ai-in-warehouse-management"
SCMR_MIT = "Supply Chain Management Review / MIT Intelligent Logistics Systems Lab (2025), \"AI's new role in running the warehouse\" - https://www.scmr.com/article/ais-new-role-in-running-the-warehouse"
FISHBOWL = "Fishbowl (2025), \"The impact and implementation of AI in warehouse management\" - https://www.fishbowlinventory.com/blog/how-ai-is-transforming-warehouse-management"
IBM_INV = "IBM (2026), \"What is AI Inventory Management?\" - https://www.ibm.com/think/topics/ai-inventory-management"
VIMAAN = "VIMAAN (2026), \"Introduction to the AI Warehouse\" - https://vimaan.ai/introduction-to-the-ai-warehouse/"
MODULA = "Modula (2026), \"AI For Warehouse Management\" - https://modula.us/blog/ai-for-warehouse-management/"

ACTIVITIES = [
    # ---------------- Process A: Procurement ----------------
    {
        "process_key": "A",
        "name": "Purchase requisition intake & PO creation",
        "description": "Receiving purchase requests and generating purchase orders against approved suppliers/contracts.",
        "frequency": "daily",
        "data_intensity": "medium",
        "roles": [{"name": "Procurement Analyst", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.85,
            "impact_type": "automate",
            "rationale": "PO processing is already one of the most common live AI/automation use cases reported by procurement leaders, and is highly rules-based.",
            "evidence_source": HACKETT,
            "confidence_score": 0.8,
        },
        "future_responsibility": "Shifts from manual PO entry to reviewing AI-flagged exceptions and approving edge cases the system can't resolve on its own.",
    },
    {
        "process_key": "A",
        "name": "Invoice / three-way matching",
        "description": "Reconciling purchase order, goods receipt, and invoice before payment approval.",
        "frequency": "daily",
        "data_intensity": "medium",
        "roles": [{"name": "Procurement Analyst", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.8,
            "impact_type": "automate",
            "rationale": "Repetitive, rules-based reconciliation task; KPMG estimates place this class of transactional work at the high end of automation potential.",
            "evidence_source": LIGHTSOURCE,
            "confidence_score": 0.75,
        },
        "future_responsibility": "Time reallocated to investigating mismatches AI cannot auto-resolve and improving matching rules.",
    },
    {
        "process_key": "A",
        "name": "Spend data analysis & savings identification",
        "description": "Analyzing historical spend to find cost-saving opportunities and category trends.",
        "frequency": "monthly",
        "data_intensity": "high",
        "roles": [
            {"name": "Procurement Analyst", "involvement_level": "primary"},
            {"name": "Procurement Manager", "involvement_level": "reviewer"},
        ],
        "ai_impact": {
            "automation_potential": 0.6,
            "impact_type": "augment",
            "rationale": "ML pattern-finding in spend data is now standard tooling, but translating findings into negotiation strategy remains a human judgment call.",
            "evidence_source": SUPLARI_2035,
            "confidence_score": 0.7,
        },
        "future_responsibility": "Analyst spends less time building reports and more time interpreting AI-surfaced insights and briefing category strategy.",
    },
    {
        "process_key": "A",
        "name": "Supplier discovery & qualification",
        "description": "Identifying and vetting new potential suppliers against capability and risk criteria.",
        "frequency": "monthly",
        "data_intensity": "high",
        "roles": [{"name": "Category Buyer", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.5,
            "impact_type": "augment",
            "rationale": "AI can analyze supplier capabilities, market conditions, and risk factors to recommend candidates, but qualification judgment stays with the buyer.",
            "evidence_source": AOP_STATE,
            "confidence_score": 0.65,
        },
        "future_responsibility": "Buyer reviews AI-ranked supplier shortlists rather than manually screening the full market.",
    },
    {
        "process_key": "A",
        "name": "Strategic sourcing / RFP evaluation",
        "description": "Running RFP/RFQ processes and evaluating supplier proposals against sourcing criteria.",
        "frequency": "monthly",
        "data_intensity": "high",
        "roles": [
            {"name": "Category Buyer", "involvement_level": "primary"},
            {"name": "Procurement Manager", "involvement_level": "reviewer"},
        ],
        "ai_impact": {
            "automation_potential": 0.45,
            "impact_type": "augment",
            "rationale": "AI assists in comparing bids and market conditions, but final sourcing decisions require human judgment on strategic fit.",
            "evidence_source": AOP_STATE,
            "confidence_score": 0.6,
        },
        "future_responsibility": "RFP scoring becomes AI-assisted; buyers focus on strategic weighting and supplier relationship factors AI can't quantify.",
    },
    {
        "process_key": "A",
        "name": "Supplier negotiation",
        "description": "Negotiating pricing, terms, and service levels with suppliers.",
        "frequency": "ad-hoc",
        "data_intensity": "medium",
        "roles": [
            {"name": "Procurement Manager", "involvement_level": "primary"},
            {"name": "Category Buyer", "involvement_level": "secondary"},
        ],
        "ai_impact": {
            "automation_potential": 0.25,
            "impact_type": "augment",
            "rationale": "Final negotiations and complex judgment calls consistently remain human-led across current industry analyses, even as prep work is AI-assisted.",
            "evidence_source": SUPLARI_2036,
            "confidence_score": 0.7,
        },
        "future_responsibility": "AI prepares negotiation briefs (market rates, supplier history); the human leads the actual negotiation.",
    },
    {
        "process_key": "A",
        "name": "Contract drafting & clause review",
        "description": "Drafting new supplier contracts and reviewing clauses for standard compliance.",
        "frequency": "weekly",
        "data_intensity": "medium",
        "roles": [{"name": "Contract Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.7,
            "impact_type": "automate",
            "rationale": "Automated contract generation and clause analysis lets one contract manager handle significantly more agreements than manual drafting allows.",
            "evidence_source": SUPLARI_2035,
            "confidence_score": 0.7,
        },
        "future_responsibility": "Contract Manager reviews AI-drafted contracts and handles only non-standard clause negotiation.",
    },
    {
        "process_key": "A",
        "name": "Contract lifecycle monitoring / renewal alerts",
        "description": "Tracking contract expiry, renewal windows, and compliance obligations.",
        "frequency": "weekly",
        "data_intensity": "low",
        "roles": [{"name": "Contract Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.8,
            "impact_type": "automate",
            "rationale": "Rules-based tracking of dates and obligations is well suited to automation, freeing managers from manual calendar tracking.",
            "evidence_source": SUPLARI_2035,
            "confidence_score": 0.75,
        },
        "future_responsibility": "System auto-flags renewals; Contract Manager only engages for renegotiation decisions.",
    },
    {
        "process_key": "A",
        "name": "Complex / high-value contract negotiation",
        "description": "Negotiating legally or financially complex contracts requiring specialized judgment.",
        "frequency": "ad-hoc",
        "data_intensity": "medium",
        "roles": [{"name": "Contract Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.2,
            "impact_type": "augment",
            "rationale": "Legal complexity and final judgment on high-stakes terms keep this human-led even as routine drafting automates around it.",
            "evidence_source": SUPLARI_2035,
            "confidence_score": 0.65,
        },
        "future_responsibility": "AI flags risk clauses and precedent; the manager retains full ownership of the negotiation itself.",
    },
    {
        "process_key": "A",
        "name": "Supplier risk monitoring",
        "description": "Ongoing monitoring of supplier financial health, compliance, and delivery risk.",
        "frequency": "weekly",
        "data_intensity": "high",
        "roles": [{"name": "Procurement Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.55,
            "impact_type": "augment",
            "rationale": "Continuous monitoring is increasingly AI-assisted through automated risk signals, with humans still deciding on response actions.",
            "evidence_source": SCMR_GARTNER,
            "confidence_score": 0.6,
        },
        "future_responsibility": "Manager responds to AI-generated risk alerts rather than manually tracking supplier health metrics.",
    },
    {
        "process_key": "A",
        "name": "AI sourcing-tool oversight & governance",
        "description": "Governing and validating the outputs of AI agents used in sourcing workflows.",
        "frequency": "weekly",
        "data_intensity": "medium",
        "roles": [{"name": "Procurement Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.0,
            "impact_type": "create-new",
            "rationale": "New AI-era roles such as procurement business architect and agentic AI portfolio manager are emerging specifically to govern these tools.",
            "evidence_source": SCMR_GARTNER,
            "confidence_score": 0.55,
        },
        "future_responsibility": "Entirely new responsibility: validating AI agent recommendations and maintaining sourcing-tool governance standards.",
    },

    # ---------------- Process B: Inventory Management ----------------
    {
        "process_key": "B",
        "name": "Demand forecasting",
        "description": "Predicting future product demand from historical sales and market signals.",
        "frequency": "weekly",
        "data_intensity": "high",
        "roles": [{"name": "Inventory Analyst", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.75,
            "impact_type": "automate",
            "rationale": "Predictive analytics and ML-based forecasting are now standard tooling for demand and inventory planning.",
            "evidence_source": ORACLE_WMS,
            "confidence_score": 0.75,
        },
        "future_responsibility": "Analyst validates and adjusts AI forecasts for known market anomalies rather than building forecasts manually.",
    },
    {
        "process_key": "B",
        "name": "Reorder point / replenishment calculation",
        "description": "Calculating when and how much stock to reorder per SKU/location.",
        "frequency": "weekly",
        "data_intensity": "high",
        "roles": [{"name": "Inventory Analyst", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.8,
            "impact_type": "automate",
            "rationale": "AI optimizes replenishment as a core inventory-management function, combining demand trends and turnover data.",
            "evidence_source": IBM_INV,
            "confidence_score": 0.75,
        },
        "future_responsibility": "Replenishment runs automatically; analyst manages exceptions like supplier disruptions.",
    },
    {
        "process_key": "B",
        "name": "Inventory optimization strategy (safety stock policy)",
        "description": "Setting safety stock levels and overall inventory policy by category.",
        "frequency": "monthly",
        "data_intensity": "medium",
        "roles": [
            {"name": "Inventory Analyst", "involvement_level": "primary"},
            {"name": "Warehouse Manager", "involvement_level": "secondary"},
        ],
        "ai_impact": {
            "automation_potential": 0.5,
            "impact_type": "augment",
            "rationale": "AI recommends storage/stock configurations from product and demand data, but overall policy remains a strategic human decision.",
            "evidence_source": ORACLE_WMS,
            "confidence_score": 0.6,
        },
        "future_responsibility": "Policy-setting becomes a review of AI-recommended configurations rather than manual calculation.",
    },
    {
        "process_key": "B",
        "name": "Cycle counting",
        "description": "Periodic physical verification of inventory accuracy.",
        "frequency": "weekly",
        "data_intensity": "medium",
        "roles": [{"name": "Warehouse Associate", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.7,
            "impact_type": "automate",
            "rationale": "Computer vision and barcode/QR scanning increasingly handle real-time inventory updates, reducing manual counting.",
            "evidence_source": VIMAAN,
            "confidence_score": 0.7,
        },
        "future_responsibility": "Associate shifts from manual counting to verifying AI-flagged discrepancies.",
    },
    {
        "process_key": "B",
        "name": "Stock discrepancy investigation",
        "description": "Investigating root causes when recorded and physical inventory don't match.",
        "frequency": "weekly",
        "data_intensity": "medium",
        "roles": [{"name": "Inventory Analyst", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.4,
            "impact_type": "augment",
            "rationale": "AI flags anomalies and discrepancies automatically, but root-cause investigation still requires human follow-up.",
            "evidence_source": VIMAAN,
            "confidence_score": 0.6,
        },
        "future_responsibility": "Analyst investigates only AI-flagged high-confidence discrepancies instead of scanning all records manually.",
    },
    {
        "process_key": "B",
        "name": "Supplier lead-time & demand-pattern analysis",
        "description": "Analyzing supplier delivery reliability and seasonal demand patterns.",
        "frequency": "monthly",
        "data_intensity": "high",
        "roles": [{"name": "Inventory Analyst", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.55,
            "impact_type": "augment",
            "rationale": "Pattern detection across supplier and demand data is automatable; interpreting implications for sourcing strategy stays human.",
            "evidence_source": IBM_INV,
            "confidence_score": 0.6,
        },
        "future_responsibility": "Analyst focuses on strategic implications of AI-surfaced patterns rather than raw data crunching.",
    },
    {
        "process_key": "B",
        "name": "Inventory reporting & dashboards",
        "description": "Producing recurring inventory status reports for stakeholders.",
        "frequency": "weekly",
        "data_intensity": "low",
        "roles": [{"name": "Inventory Analyst", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.75,
            "impact_type": "automate",
            "rationale": "Generative AI is increasingly used for automated documentation and reporting tasks in supply chain operations.",
            "evidence_source": SCMR_MIT,
            "confidence_score": 0.7,
        },
        "future_responsibility": "Reports generate automatically; analyst adds commentary and escalates only notable trends.",
    },

    # ---------------- Process C: Warehouse Operations ----------------
    {
        "process_key": "C",
        "name": "Order picking",
        "description": "Retrieving items from storage locations to fulfill customer orders.",
        "frequency": "daily",
        "data_intensity": "low",
        "roles": [{"name": "Warehouse Associate", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.75,
            "impact_type": "automate",
            "rationale": "Picking robots using computer vision are widely deployed to recognize and retrieve items efficiently.",
            "evidence_source": MECALUX,
            "confidence_score": 0.7,
        },
        "future_responsibility": "Associate shifts toward exception picking and overseeing robotic picking systems.",
    },
    {
        "process_key": "C",
        "name": "Packing & sorting",
        "description": "Packing picked items and sorting them for shipment.",
        "frequency": "daily",
        "data_intensity": "low",
        "roles": [{"name": "Warehouse Associate", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.7,
            "impact_type": "automate",
            "rationale": "Automated sorting and packing systems handle repetitive, physically strenuous tasks with increased accuracy.",
            "evidence_source": FISHBOWL,
            "confidence_score": 0.7,
        },
        "future_responsibility": "Associate manages and monitors automated packing lines rather than packing manually.",
    },
    {
        "process_key": "C",
        "name": "Pick-route optimization",
        "description": "Determining the most efficient path for pickers through the warehouse.",
        "frequency": "daily",
        "data_intensity": "medium",
        "roles": [
            {"name": "Warehouse Manager", "involvement_level": "reviewer"},
            {"name": "Logistics Coordinator", "involvement_level": "secondary"},
        ],
        "ai_impact": {
            "automation_potential": 0.8,
            "impact_type": "automate",
            "rationale": "AI analyzes warehouse layout and order patterns to compute optimal picking routes, minimizing travel distance automatically.",
            "evidence_source": "Kanerika (2025), \"How AI in Warehouse Management 2025 is Transforming Operations\" - https://medium.com/@kanerika/how-ai-in-warehouse-management-2025-is-transforming-operations-78e877144fd9",
            "confidence_score": 0.7,
        },
        "future_responsibility": "Routes generate automatically; manager only intervenes for layout changes or major disruptions.",
    },
    {
        "process_key": "C",
        "name": "Warehouse layout & slotting optimization",
        "description": "Deciding where products are stored to optimize space and retrieval efficiency.",
        "frequency": "monthly",
        "data_intensity": "high",
        "roles": [{"name": "Warehouse Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.5,
            "impact_type": "augment",
            "rationale": "AI recommends efficient storage configurations from product size, demand, and turnover data, but final layout decisions remain managerial.",
            "evidence_source": ORACLE_WMS,
            "confidence_score": 0.6,
        },
        "future_responsibility": "Manager evaluates and approves AI-recommended layouts rather than designing them manually.",
    },
    {
        "process_key": "C",
        "name": "Labor / task assignment & scheduling",
        "description": "Assigning warehouse staff to tasks and shifts based on workload.",
        "frequency": "daily",
        "data_intensity": "medium",
        "roles": [{"name": "Warehouse Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.45,
            "impact_type": "augment",
            "rationale": "AI-powered workforce systems monitor performance metrics to inform task assignment, but scheduling decisions stay with the manager.",
            "evidence_source": MODULA,
            "confidence_score": 0.55,
        },
        "future_responsibility": "Manager uses AI-recommended staffing plans rather than building schedules from scratch.",
    },
    {
        "process_key": "C",
        "name": "Predictive equipment maintenance",
        "description": "Anticipating equipment failures before they cause downtime.",
        "frequency": "weekly",
        "data_intensity": "medium",
        "roles": [{"name": "Warehouse Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.7,
            "impact_type": "automate",
            "rationale": "Predictive analytics for equipment maintenance is a well-established AI application in warehouse operations.",
            "evidence_source": SCMR_MIT,
            "confidence_score": 0.7,
        },
        "future_responsibility": "Manager acts on AI-generated maintenance alerts instead of manual inspection schedules.",
    },
    {
        "process_key": "C",
        "name": "Safety monitoring / hazard detection",
        "description": "Monitoring the warehouse floor for safety hazards and unsafe conditions.",
        "frequency": "daily",
        "data_intensity": "medium",
        "roles": [{"name": "Warehouse Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.5,
            "impact_type": "augment",
            "rationale": "AI monitors and alerts on hazardous conditions in real time, while humans remain responsible for responding to incidents.",
            "evidence_source": MODULA,
            "confidence_score": 0.6,
        },
        "future_responsibility": "Manager responds to AI safety alerts rather than relying solely on manual floor walks.",
    },
    {
        "process_key": "C",
        "name": "Shipment documentation & carrier coordination",
        "description": "Preparing shipping documents and coordinating pickup/delivery with carriers.",
        "frequency": "daily",
        "data_intensity": "medium",
        "roles": [{"name": "Logistics Coordinator", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.75,
            "impact_type": "automate",
            "rationale": "NLP automates data extraction from shipping notices, invoices, and delivery receipts, reducing manual document processing.",
            "evidence_source": ORACLE_WMS,
            "confidence_score": 0.7,
        },
        "future_responsibility": "Coordinator reviews AI-prepared documentation and handles only carrier exceptions.",
    },
    {
        "process_key": "C",
        "name": "Exception management (delays, damaged goods)",
        "description": "Handling shipment delays, damaged goods, and other fulfillment exceptions.",
        "frequency": "daily",
        "data_intensity": "medium",
        "roles": [
            {"name": "Logistics Coordinator", "involvement_level": "primary"},
            {"name": "Warehouse Manager", "involvement_level": "secondary"},
        ],
        "ai_impact": {
            "automation_potential": 0.3,
            "impact_type": "augment",
            "rationale": "MIT research finds automation elevates frontline roles toward exception management rather than eliminating them, as routine work is automated around this activity.",
            "evidence_source": SCMR_MIT,
            "confidence_score": 0.65,
        },
        "future_responsibility": "This activity grows in relative importance as routine work automates elsewhere; coordinator role becomes more exception-focused.",
    },
    {
        "process_key": "C",
        "name": "AI system oversight & performance tuning",
        "description": "Monitoring and tuning the AI/automation systems running warehouse operations.",
        "frequency": "weekly",
        "data_intensity": "medium",
        "roles": [{"name": "Warehouse Manager", "involvement_level": "primary"}],
        "ai_impact": {
            "automation_potential": 0.0,
            "impact_type": "create-new",
            "rationale": "Generative AI is now used to engineer operational improvements directly (layout design, process-flow optimization), creating a new managerial responsibility to oversee and tune these systems.",
            "evidence_source": SCMR_MIT,
            "confidence_score": 0.55,
        },
        "future_responsibility": "Entirely new responsibility: validating AI-generated operational changes before they go live on the floor.",
    },
]

# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------


def seed(session) -> None:
    if session.query(Industry).filter_by(name=INDUSTRY["name"]).first():
        print(f"Industry '{INDUSTRY['name']}' already seeded — skipping (idempotent).")
        return

    industry = Industry(**INDUSTRY)
    session.add(industry)
    session.flush()  # get industry.id

    process_by_key = {}
    for p in PROCESSES:
        proc = Process(industry_id=industry.id, name=p["name"], description=p["description"])
        session.add(proc)
        session.flush()
        process_by_key[p["key"]] = proc

    role_by_name = {}
    for r in ROLES:
        role = Role(**r)
        session.add(role)
        session.flush()
        role_by_name[r["name"]] = role

    for a in ACTIVITIES:
        process = process_by_key[a["process_key"]]
        activity = Activity(
            process_id=process.id,
            name=a["name"],
            description=a["description"],
            frequency=a["frequency"],
            data_intensity=a["data_intensity"],
        )
        session.add(activity)
        session.flush()

        for r in a["roles"]:
            session.add(
                RoleActivity(
                    role_id=role_by_name[r["name"]].id,
                    activity_id=activity.id,
                    involvement_level=r["involvement_level"],
                )
            )

        impact = a["ai_impact"]
        session.add(
            AIImpact(
                activity_id=activity.id,
                automation_potential=impact["automation_potential"],
                impact_type=impact["impact_type"],
                rationale=impact["rationale"],
                evidence_source=impact["evidence_source"],
                confidence_score=impact["confidence_score"],
            )
        )

        # One future_responsibility row per role attached to this activity,
        # so the reasoning engine can join role -> activity -> future_responsibility directly.
        for r in a["roles"]:
            session.add(
                FutureResponsibility(
                    role_id=role_by_name[r["name"]].id,
                    activity_id=activity.id,
                    description=a["future_responsibility"],
                )
            )

    session.commit()

    n_activities = len(ACTIVITIES)
    n_roles = len(ROLES)
    n_processes = len(PROCESSES)
    n_links = sum(len(a["roles"]) for a in ACTIVITIES)
    print(
        f"Seeded 1 industry, {n_processes} processes, {n_roles} roles, "
        f"{n_activities} activities, {n_links} role-activity links, "
        f"{n_activities} AI impact records."
    )


def main():
    engine = get_engine()
    init_db(engine)
    session = get_session(engine)
    try:
        seed(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()