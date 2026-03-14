# faq.py ✅ Common answers + domain library

knowledge_base = {
    "pitch": """
📘 **6-Month Job Ready Business Analyst Program**

✅ Fresher to IT Transition Course with 100% Placement Guarantee

✅ You will learn:
• BA Fundamentals + SDLC (Waterfall & Agile Scrum)
• BRD / FRD / User Stories / Acceptance Criteria
• Tools: Jira, SQL, Power BI, Tableau, Balsamiq, Draw.io, MS Visio, Excel, Azure
• 3+ Real-Time Domain Projects
• 100% Placement Guarantee + Mock Interviews

Training Structure: 2 Hours Theory + 4 Hours Hands-On Practical Training daily.

✅ Free Hostel Facility for Outstation Students
✅ Up to 15% Discount Available

If you want the full roadmap, click **Book Free Demo**.
""".strip(),

    "duration": "The program duration is **6 months** — a comprehensive Job Ready Business Analyst program covering fundamentals, tools training, real-time projects, documentation practice, mock interviews and placement support.",

    "course_structure": """
Course Structure:

• 6 Months Business Analyst Training Program
• 2 Hours Theory + 4 Hours Hands-On Practical Daily
• Training on Industry Tools

Tools Covered:

• Jira
• SQL
• Tableau
• Power BI
• Balsamiq
• Draw.io
• Agile & Scrum Practices

Projects:

• 3 Capstone Projects
• 2 Real-Time Live Projects
""".strip(),

    "program_benefits": """
Program Benefits of COEPD Business Analyst Training:

• Industry-Focused Training Program
• Suitable for IT and Non-IT Professionals
• No Coding Required
• Real Business Analyst Case Studies
• Global Recognition Certificate (IIBA 40 PD Hours)
• Resume Preparation Support
• Mock Interview Preparation
• Career Transition Guidance
• Dedicated Placement Assistance
• Hostel Facility for Outstation Candidates
• Up to 15% Early Registration Discount
""".strip(),

    "placement": """
✅ **100% Placement Guarantee** includes:
• Dedicated placement support team
• Resume preparation & LinkedIn optimization
• Mock interviews & interview training
• Interview scheduling with partner companies
• Profile building support

Most candidates receive offers within **3–5 interviews** through our placement process.
""".strip(),

    "fees": """
The course fee depends on current batch offers.

Currently we provide **up to 15% discount for early registrations**.

Our program advisor will explain the exact fee during the **Free Demo Session**.

Would you like to join the upcoming demo?
""".strip(),

    "placement_programs": """
**6-Month Job Ready Business Analyst Program** with 100% Placement Guarantee.

Our dedicated placement team provides:
• Resume preparation & optimization
• Mock interviews & interview training
• Interview scheduling with 2700+ hiring partner companies
• Soft skills training

Most candidates receive offers within **3–5 interviews**.

Would you like to book a free demo to learn more?
""".strip(),

    "internship_programs": """
Our **6-Month Job Ready Business Analyst Program** includes real-time project training as part of Stage 2.

Students work on live case studies, BRD/FRD documentation, and gain hands-on experience with Power BI, SQL, Excel and Agile Scrum.

✅ 2 Hours Theory + 4 Hours Practical Training Daily
✅ 100% Placement Guarantee
✅ Free Hostel Facility Available

Book a free demo to learn more about program benefits and batch offers!
""".strip(),

    "batch_timings": """
Batch timings depend on your preference:

• Weekday (Morning / Evening)
• Weekend (Saturday / Sunday)

Click **Book Free Demo** and we’ll confirm the next available slot.
""".strip(),
}

DOMAIN_LIBRARY = {
    "finance": {
        "label": "Finance / Banking",
        "title": "🏦 Finance / Banking BA Roles (High Demand)",
        "roles": [
            "Core Banking BA (CBS)",
            "Digital Banking BA (Mobile / Internet Banking)",
            "Payments BA (UPI / IMPS / NEFT / RTGS)",
            "Risk & Compliance BA (KYC / AML)",
            "Loans & Credit BA (Retail / SME / Corporate)",
        ],
        "tools": ["Jira", "Confluence", "SQL", "Power BI/Tableau", "Visio", "Swagger/Postman"],
        "projects": [
            "UPI payments: user stories + test cases + UAT plan",
            "Loan journey: BRD + process map + backlog",
            "KYC/AML rules: acceptance criteria + edge cases",
        ],
        "salary": "India: ₹6–18 LPA | Global: $60k–120k",
    },

    "healthcare": {
        "label": "Healthcare",
        "title": "🏥 Healthcare BA Roles",
        "roles": [
            "Hospital Management BA",
            "Clinical Systems BA (HIS/EMR/EHR)",
            "Medical Billing / Claims BA",
            "Healthcare Data BA",
            "Compliance BA",
        ],
        "tools": ["Jira", "SQL", "Confluence", "Power BI", "Visio", "Documentation"],
        "projects": [
            "Appointment workflow: process map + improvements",
            "Claims processing: business rules + UAT scenarios",
            "Hospital dashboard: KPIs + reporting",
        ],
        "salary": "India: ₹5–15 LPA | Global: $55k–110k",
    },

    "retail": {
        "label": "Retail / E-commerce",
        "title": "🛒 Retail / E-commerce BA Roles",
        "roles": [
            "E-commerce BA",
            "Retail Operations BA",
            "Customer Experience BA",
            "Inventory / Supply BA",
            "Pricing & Promotions BA",
        ],
        "tools": ["Jira", "Confluence", "SQL", "Power BI", "Figma/Balsamiq", "Analytics basics"],
        "projects": [
            "Checkout drop-off: analysis → requirements",
            "Returns/refunds: stories + validations",
            "Inventory reorder logic: rules + dashboard",
        ],
        "salary": "India: ₹5–16 LPA | Global: $55k–115k",
    },

    "insurance": {
        "label": "Insurance",
        "title": "🛡 Insurance BA Roles",
        "roles": [
            "Policy Administration BA",
            "Claims Processing BA",
            "Underwriting BA",
            "Risk Analytics BA",
            "Compliance BA",
        ],
        "tools": ["Jira", "Confluence", "SQL", "Power BI", "Visio", "Documentation"],
        "projects": [
            "Claims flow: rules + fraud checks + UAT plan",
            "Policy issuance: validations + acceptance criteria",
            "Underwriting dashboard: KPIs + reporting",
        ],
        "salary": "India: ₹5–15 LPA | Global: $55k–110k",
    },

    "telecom": {
        "label": "Telecom",
        "title": "📡 Telecom BA Roles",
        "roles": [
            "Telecom Billing BA",
            "CRM / Customer Service BA",
            "Network Operations BA",
            "Digital Services BA",
            "Product BA (Plans/5G)",
        ],
        "tools": ["Jira", "Confluence", "SQL", "Power BI", "Visio", "API basics"],
        "projects": [
            "Recharge/plan change: stories + validations",
            "Billing disputes: flow + KPIs",
            "Churn dashboard: KPIs + recommendations",
        ],
        "salary": "India: ₹5–16 LPA | Global: $55k–115k",
    },

    "logistics": {
        "label": "Logistics / Supply Chain",
        "title": "🚚 Logistics / Supply Chain BA Roles",
        "roles": [
            "Warehouse Management BA",
            "Transportation Management BA",
            "Supply Chain Analytics BA",
            "Inventory Optimization BA",
            "Operations BA",
        ],
        "tools": ["Confluence", "SQL", "Power BI", "Jira", "Visio", "Process mapping"],
        "projects": [
            "Delivery tracking: workflow + KPIs",
            "Warehouse picking optimization: requirements + UAT",
            "Inventory forecasting dashboard",
        ],
        "salary": "India: ₹5–15 LPA | Global: $55k–110k",
    },

    "manufacturing": {
        "label": "Manufacturing",
        "title": "🏭 Manufacturing BA Roles",
        "roles": [
            "ERP/SAP BA (Manufacturing)",
            "Production Planning BA",
            "Quality Process BA",
            "Operations Excellence BA",
            "Supply Chain BA",
        ],
        "tools": ["Confluence", "SQL", "Power BI", "Process mapping", "ERP basics", "Jira"],
        "projects": [
            "Production KPI dashboard",
            "Defect tracking workflow",
            "Procure-to-pay process mapping",
        ],
        "salary": "India: ₹5–16 LPA | Global: $55k–115k",
    },

    "pharma": {
        "label": "Pharmaceutical",
        "title": "💊 Pharma BA Roles",
        "roles": [
            "Clinical Trial BA",
            "Regulatory/Compliance BA",
            "Pharma Supply Chain BA",
            "R&D Process BA",
            "Data BA",
        ],
        "tools": ["Confluence", "SQL", "Power BI", "Documentation", "Process mapping", "Jira"],
        "projects": [
            "Clinical data workflow requirements",
            "Compliance reporting rules",
            "Supply chain KPI dashboard",
        ],
        "salary": "India: ₹6–18 LPA | Global: $60k–120k",
    },

    "education": {
        "label": "Education / EdTech",
        "title": "🎓 Education / EdTech BA Roles",
        "roles": [
            "EdTech Product BA",
            "Learning Platform (LMS) BA",
            "Student Analytics BA",
            "Growth/Funnel BA",
            "Operations BA",
        ],
        "tools": ["Confluence", "SQL", "Power BI", "Analytics basics", "Jira", "Figma/Balsamiq"],
        "projects": [
            "Enrollment funnel improvements",
            "LMS feature stories + AC",
            "Student success dashboard",
        ],
        "salary": "India: ₹5–16 LPA | Global: $55k–115k",
    },

    "real_estate": {
        "label": "Real Estate",
        "title": "🏢 Real Estate BA Roles",
        "roles": [
            "Property Management BA",
            "Real Estate CRM BA",
            "Construction Process BA",
            "Mortgage / Lending BA",
            "Data BA",
        ],
        "tools": ["Confluence", "SQL", "Power BI", "Jira", "Process mapping", "Documentation"],
        "projects": [
            "Lead-to-site-visit process mapping",
            "Rental workflow requirements",
            "Mortgage journey validations",
        ],
        "salary": "India: ₹5–16 LPA | Global: $55k–115k",
    },

    "energy": {
        "label": "Energy / Utilities",
        "title": "⚡ Energy / Utilities BA Roles",
        "roles": [
            "Utility Billing BA",
            "Operations & Maintenance BA",
            "Energy Data BA",
            "Compliance BA",
            "Renewables BA",
        ],
        "tools": ["Confluence", "SQL", "Power BI", "Process mapping", "Jira"],
        "projects": [
            "Billing dispute workflow",
            "Energy usage KPI dashboard",
            "Compliance checklist automation",
        ],
        "salary": "India: ₹6–18 LPA | Global: $60k–120k",
    },

    "government": {
        "label": "Government / Public Sector",
        "title": "🏛 Public Sector BA Roles",
        "roles": [
            "E-Governance BA",
            "Citizen Services BA",
            "Process Improvement BA",
            "Audit/Compliance BA",
            "Public Data BA",
        ],
        "tools": ["Documentation", "Confluence", "Power BI", "Process mapping", "Jira"],
        "projects": [
            "Citizen service digitization (BRD + backlog)",
            "Department KPI dashboard",
            "Compliance tracking system",
        ],
        "salary": "India: ₹5–15 LPA | Global: $55k–110k",
    },

    "technology": {
        "label": "Technology / IT / SaaS",
        "title": "💻 IT / SaaS Product BA Roles",
        "roles": [
            "Agile Business Analyst",
            "Product BA (SaaS)",
            "API/Integrations BA",
            "Digital Transformation BA",
            "Data Product BA",
        ],
        "tools": ["Jira", "Confluence", "SQL", "Power BI/Tableau", "Figma/Balsamiq", "Swagger/Postman"],
        "projects": [
            "SaaS feature: stories + AC + UAT",
            "API integration requirements + error handling",
            "Product metrics dashboard",
        ],
        "salary": "India: ₹6–22 LPA | Global: $65k–140k",
    },
}