(function () {
  const DOMAINS = [
    {
      name: "Banking",
      icon: "bank",
      projects: ["Loan Processing System", "Credit Risk Analysis Dashboard", "Customer Onboarding System"]
    },
    {
      name: "Finance",
      icon: "finance",
      projects: ["Portfolio Management System", "Trading Platform Analytics", "Financial Reporting Dashboard"]
    },
    {
      name: "Insurance",
      icon: "shield",
      projects: ["Policy Management System", "Claim Processing Workflow", "Fraud Detection Dashboard"]
    },
    {
      name: "Healthcare",
      icon: "health",
      projects: ["Hospital Management System", "Patient Data Analytics", "Appointment Scheduling Platform"]
    },
    {
      name: "Pharmaceutical",
      icon: "pill",
      projects: ["Drug Trial Management", "Pharmacy Inventory System", "Regulatory Compliance Tracker"]
    },
    {
      name: "Retail",
      icon: "cart",
      projects: ["Inventory Management System", "Customer Recommendation Engine", "POS Analytics Dashboard"]
    },
    {
      name: "E-Commerce",
      icon: "monitor",
      projects: ["Online Shopping Platform", "Payment Gateway Integration", "Vendor Management System"]
    },
    {
      name: "Manufacturing",
      icon: "factory",
      projects: ["Supply Chain Optimization System", "Production Planning Dashboard", "Inventory Forecasting System"]
    },
    {
      name: "Telecommunications",
      icon: "target",
      projects: ["Customer Billing System", "Telecom CRM Platform", "Network Monitoring Dashboard"]
    },
    {
      name: "Supply Chain",
      icon: "truck",
      projects: ["Fleet Management System", "Warehouse Management Platform", "Logistics Tracking Dashboard"]
    },
    {
      name: "Education Technology",
      icon: "graduation",
      projects: ["Learning Management System", "Student Performance Analytics", "Online Examination Platform"]
    },
    {
      name: "Government Projects",
      icon: "building",
      projects: ["Citizen Services Portal", "Public Grievance System", "E-Governance Dashboard"]
    }
  ];

  function iconSvg(kind) {
    const common = 'stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"';
    const icons = {
      bank: `<svg viewBox="0 0 24 24" aria-hidden="true"><path ${common} d="M3 10h18M4 20h16M6 10v10M10 10v10M14 10v10M18 10v10M12 4l9 4H3l9-4z"/></svg>`,
      finance: `<svg viewBox="0 0 24 24" aria-hidden="true"><path ${common} d="M5 19h14M7 16l3-3 3 2 4-5"/><circle cx="7" cy="16" r="1.2"/><circle cx="10" cy="13" r="1.2"/><circle cx="13" cy="15" r="1.2"/><circle cx="17" cy="10" r="1.2"/></svg>`,
      shield: `<svg viewBox="0 0 24 24" aria-hidden="true"><path ${common} d="M12 3l7 3v6c0 4.5-2.8 7.5-7 9-4.2-1.5-7-4.5-7-9V6l7-3z"/><path ${common} d="M9 12l2 2 4-4"/></svg>`,
      health: `<svg viewBox="0 0 24 24" aria-hidden="true"><path ${common} d="M12 5v14M5 12h14"/></svg>`,
      pill: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect ${common} x="6" y="3" width="12" height="18" rx="4"/><path ${common} d="M9 9h6M9 13h6"/></svg>`,
      cart: `<svg viewBox="0 0 24 24" aria-hidden="true"><path ${common} d="M4 6h2l1.2 7.2a2 2 0 0 0 2 1.8h7.8a2 2 0 0 0 2-1.6L20 8H7"/><circle cx="10" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/></svg>`,
      monitor: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect ${common} x="4" y="4" width="16" height="12" rx="2"/><path ${common} d="M9 20h6M12 16v4"/></svg>`,
      factory: `<svg viewBox="0 0 24 24" aria-hidden="true"><path ${common} d="M3 20V8l5 3V8l5 3V6l8 4v10H3z"/><path ${common} d="M8 20v-4h3v4"/></svg>`,
      target: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle ${common} cx="12" cy="12" r="8"/><circle ${common} cx="12" cy="12" r="3"/><path ${common} d="M12 4v2M20 12h-2M12 20v-2M4 12h2"/></svg>`,
      truck: `<svg viewBox="0 0 24 24" aria-hidden="true"><path ${common} d="M3 7h11v8H3zM14 10h3l3 3v2h-6z"/><circle cx="8" cy="17" r="1.7"/><circle cx="18" cy="17" r="1.7"/></svg>`,
      graduation: `<svg viewBox="0 0 24 24" aria-hidden="true"><path ${common} d="M3 9l9-5 9 5-9 5-9-5z"/><path ${common} d="M7 11v4c0 1.5 2.2 3 5 3s5-1.5 5-3v-4"/></svg>`,
      building: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect ${common} x="4" y="5" width="16" height="15" rx="2"/><path ${common} d="M8 9h2M12 9h2M16 9h0M8 13h2M12 13h2M8 17h8"/></svg>`
    };
    return icons[kind] || icons.bank;
  }

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function createCard(domain) {
    const card = document.createElement("article");
    card.className = "domain-card saas-domain-card";
    card.innerHTML = [
      '<div class="domain-icon-wrap">' + iconSvg(domain.icon) + "</div>",
      "<h3>" + escapeHtml(domain.name) + "</h3>",
      '<ul class="domain-projects">',
      domain.projects.map(function (p) {
        return "<li>" + escapeHtml(p) + "</li>";
      }).join(""),
      "</ul>"
    ].join("");
    return card;
  }

  function renderDomains() {
    const grid = document.getElementById("domain-grid");
    const counter = document.getElementById("domain-counter");
    if (!grid) return;

    grid.innerHTML = "";
    if (counter) counter.textContent = "Showing " + DOMAINS.length + " Industry Domains";

    const fragment = document.createDocumentFragment();
    DOMAINS.forEach(function (domain) {
      fragment.appendChild(createCard(domain));
    });
    grid.appendChild(fragment);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderDomains);
  } else {
    renderDomains();
  }
})();
