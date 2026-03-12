const context = window.__ADMIN_CONTEXT__ || {};
const currentRole = String(context.role || "staff").toLowerCase();
const csrfToken = String(context.csrfToken || "");

let leadChart = null;
let sourceChart = null;
let allLeads = [];
let allUsers = [];
let currentPage = 1;
const pageSize = 10;
let refreshInFlight = false;
let refreshTimer = null;

function setStatus(message, isError = false) {
  const statusEl = document.getElementById("admin-status");
  if (!statusEl) return;
  statusEl.textContent = message || "";
  statusEl.style.color = isError ? "#dc2626" : "#475569";
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function sourceBadge(source) {
  const value = String(source || "").trim().toLowerCase();
  const normalized = value === "website_form" ? "webpage" : value;
  const label = normalized === "webpage" ? "webpage" : (normalized || "unknown");
  const css = normalized === "chatbot" ? "badge badge-chatbot" : "badge badge-webpage";
  return `<span class="${css}">${escapeHtml(label)}</span>`;
}

const DOMAIN_BADGE_MAP = {
  "it": "badge-it",
  "non-it": "badge-nonit",
  "bba/bcom": "badge-bba",
  "mba": "badge-mba",
  "engineering": "badge-engineering",
  "fresh graduate": "badge-fresher",
  "other": "badge-other",
};

function domainBadge(domain) {
  const raw = String(domain || "").trim();
  if (!raw || raw === "-") return escapeHtml("-");
  const key = raw.toLowerCase();
  const cls = DOMAIN_BADGE_MAP[key] || "badge-other";
  return `<span class="badge ${cls}">${escapeHtml(raw)}</span>`;
}

function roleBadge(role) {
  const value = String(role || "staff").trim().toLowerCase();
  return `<span class="role-badge ${value}">${escapeHtml(value)}</span>`;
}

function activeBadge(isActive) {
  const active = Boolean(isActive);
  return `<span class="active-badge ${active ? "active" : "inactive"}">${active ? "active" : "inactive"}</span>`;
}

function normalizeUserActive(user) {
  const status = String(user?.status || "").trim().toLowerCase();
  if (status === "active") return true;
  if (status === "inactive") return false;
  return Boolean(user?.is_active);
}

function currentFilterDate() {
  const dateInput = document.getElementById("filter-date");
  return dateInput ? (dateInput.value || "") : "";
}

function currentFilterSource() {
  const sourceInput = document.getElementById("filter-source");
  return sourceInput ? (sourceInput.value || "all") : "all";
}

function currentFilterSearch() {
  const searchInput = document.getElementById("filter-search");
  return searchInput ? (searchInput.value || "") : "";
}

function currentFilterDomain() {
  const domainInput = document.getElementById("filter-domain");
  return domainInput ? (domainInput.value || "all") : "all";
}

function updateSectionTitle() {
  const sectionEl = document.getElementById("lead-section-title");
  if (!sectionEl) return;

  const source = currentFilterSource();
  if (source === "webpage") {
    sectionEl.textContent = "Webpage Leads";
    return;
  }
  if (source === "chatbot") {
    sectionEl.textContent = "Chatbot Leads";
    return;
  }
  sectionEl.textContent = "All Leads";
}

function updatePager() {
  const pageInfo = document.getElementById("page-info");
  const prevBtn = document.getElementById("prev-page");
  const nextBtn = document.getElementById("next-page");

  const totalPages = Math.max(1, Math.ceil(allLeads.length / pageSize));
  if (currentPage > totalPages) currentPage = totalPages;

  if (pageInfo) pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  if (prevBtn) prevBtn.disabled = currentPage <= 1;
  if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
}

async function fetchJson(url, fallbackErrorMessage, options = {}) {
  const fullUrl = (window.__API_BASE__ || "") + url;
  const requestOptions = {
    headers: { Accept: "application/json", ...(options.headers || {}) },
    cache: "no-store",
    credentials: "include",
    ...options,
  };

  const method = String(requestOptions.method || "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && csrfToken) {
    requestOptions.headers["X-CSRF-Token"] = csrfToken;
  }

  try {
    const response = await fetch(fullUrl, requestOptions);
    if (response.status === 401) {
      window.location.href = "/admin";
      throw new Error("UNAUTHORIZED");
    }
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      return {};
    }
    const data = await response.json();
    if (data && data.success === false) {
      throw new Error(data.error || fallbackErrorMessage || "Request failed");
    }
    return data;
  } catch (error) {
    console.error(fallbackErrorMessage, error);
    throw error;
  }
}

function renderChart(datesRaw, countsRaw) {
  const canvas = document.getElementById("leadChart");
  if (!canvas || typeof Chart === "undefined") return;

  const dates = asArray(datesRaw).map((x) => String(x));
  const counts = asArray(countsRaw).map((x) => Number(x) || 0);
  const safeCounts = (counts.length === dates.length)
    ? counts
    : (counts.concat(new Array(Math.max(0, dates.length - counts.length)).fill(0))).slice(0, dates.length);

  if (leadChart) {
    leadChart.destroy();
    leadChart = null;
  }

  leadChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: dates,
      datasets: [
        {
          label: "Leads",
          data: safeCounts,
          borderColor: "#0f766e",
          backgroundColor: "rgba(15,118,110,0.12)",
          fill: true,
          tension: 0.25,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } },
      },
    },
  });
}

function leadStatusControl(lead) {
  const currentStatus = String(lead.working_status || "").trim();
  return `
    <div>
      <input id="status-${lead.id}" value="${escapeHtml(currentStatus)}" placeholder="lead status" />
      <button class="info status-btn" data-lead-id="${lead.id}">Update</button>
    </div>
  `;
}

function renderLeadsTable() {
  const tbody = document.getElementById("leads-body");
  if (!tbody) return;

  const rows = asArray(allLeads);
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:24px;color:#64748b">No leads found.</td></tr>';
    updatePager();
    return;
  }

  const start = (currentPage - 1) * pageSize;
  const pagedRows = rows.slice(start, start + pageSize);

  const html = pagedRows.map((lead) => {
    const id = Number(lead.id) || 0;
    const createdAt = (lead.datetime_display && lead.datetime_display !== "Unknown")
      ? lead.datetime_display
      : (lead.date_display && lead.date_display !== "Unknown")
        ? `${lead.date_display} ${lead.time_display || ""}`.trim()
        : String(lead.created_at || "");

    const whatsappCell = lead.whatsapp
      ? `<a class="wa-link" href="https://wa.me/91${escapeHtml(lead.whatsapp)}" target="_blank" rel="noopener">${escapeHtml(lead.whatsapp)}</a>`
      : "-";

    const deleteAction = currentRole === "admin"
      ? `<button class="btn-sm danger delete-btn" data-lead-id="${id}">Delete</button>`
      : "";

    return `
      <tr id="row-${id}">
        <td>${id}</td>
        <td style="font-weight:500">${escapeHtml(lead.name)}</td>
        <td>${escapeHtml(lead.phone)}</td>
        <td>${escapeHtml(lead.email)}</td>
        <td>${escapeHtml(lead.location || "-")}</td>
        <td>${domainBadge(lead.interested_domain)}</td>
        <td>${escapeHtml(lead.experience || "-")}</td>
        <td>${whatsappCell}</td>
        <td>${sourceBadge(lead.source)}</td>
        <td style="white-space:nowrap">${escapeHtml(createdAt)}</td>
        <td>${deleteAction || "-"}</td>
      </tr>
    `;
  }).join("");

  tbody.innerHTML = html;
  updatePager();
}

function renderUsersTable() {
  const tbody = document.getElementById("users-body");
  if (!tbody) return;

  if (!allUsers.length) {
    tbody.innerHTML = '<tr><td colspan="7">No staff users found.</td></tr>';
    return;
  }

  tbody.innerHTML = allUsers.map((user) => {
    const id = Number(user.id) || 0;
    const isActive = String(user.status || "inactive").toLowerCase() === "active";
    const activateBtn = isActive
      ? `<button class="secondary deactivate-btn" data-user-id="${id}">Deactivate</button>`
      : `<button class="info activate-btn" data-user-id="${id}">Activate</button>`;
    return `
      <tr>
        <td>${id}</td>
        <td>${escapeHtml(user.name)}</td>
        <td>${escapeHtml(user.email)}</td>
        <td>${roleBadge(user.role)}</td>
        <td>${activeBadge(isActive)}</td>
        <td>${escapeHtml(user.created_at || "")}</td>
        <td>
          ${activateBtn}
          <button class="secondary set-role-btn" data-role="staff" data-user-id="${id}">Set Staff</button>
          <button class="info set-role-btn" data-role="admin" data-user-id="${id}">Set Admin</button>
          <button class="danger delete-user-btn" data-user-id="${id}">Delete</button>
        </td>
      </tr>
    `;
  }).join("");
}

function renderSourceChart(leads) {
  const canvas = document.getElementById("sourceChart");
  if (!canvas || typeof Chart === "undefined") return;

  const counts = {};
  asArray(leads).forEach((l) => {
    const src = String(l.source || "unknown").toLowerCase();
    const key = src === "website_form" ? "webpage" : src;
    counts[key] = (counts[key] || 0) + 1;
  });

  const labels = Object.keys(counts);
  const data = Object.values(counts);
  const colors = ["#0f766e", "#6366f1", "#9333ea", "#f59e0b", "#ef4444", "#3b82f6"];

  if (sourceChart) { sourceChart.destroy(); sourceChart = null; }

  sourceChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors.slice(0, labels.length), borderWidth: 0 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", labels: { font: { size: 12 } } } },
    },
  });
}

async function loadAnalytics() {
  if (currentRole !== "admin") return;
  const data = await fetchJson("/admin/analytics", "Unable to fetch analytics");
  const totalEl = document.getElementById("total-leads-count");
  const todayEl = document.getElementById("today-leads-count");
  const weekEl = document.getElementById("week-leads-count");
  const monthEl = document.getElementById("month-leads-count");
  const chatbotEl = document.getElementById("chatbot-leads-count");
  const websiteEl = document.getElementById("website-leads-count");
  if (totalEl) totalEl.textContent = String(Number(data.total_leads) || 0);
  if (todayEl) todayEl.textContent = String(Number(data.today_leads) || 0);
  if (weekEl) weekEl.textContent = String(Number(data.week_leads) || 0);
  if (monthEl) monthEl.textContent = String(Number(data.month_leads) || 0);
  if (chatbotEl) chatbotEl.textContent = String(Number(data.chatbot_leads) || 0);
  if (websiteEl) websiteEl.textContent = String(Number(data.website_leads) || 0);
  renderChart(data.dates, data.counts);
  renderSourceChart(allLeads);
}

async function loadLeads() {
  const date = currentFilterDate();
  const source = currentFilterSource();
  const search = currentFilterSearch();
  const domain = currentFilterDomain();
  const queryParts = [];
  if (date) queryParts.push(`date=${encodeURIComponent(date)}`);
  if (source && source !== "all") queryParts.push(`source=${encodeURIComponent(source)}`);
  if (domain && domain !== "all") queryParts.push(`interested_domain=${encodeURIComponent(domain)}`);
  if (search) queryParts.push(`search=${encodeURIComponent(search)}`);
  const query = queryParts.length ? `?${queryParts.join("&")}` : "";

  const payload = await fetchJson(`/admin/leads${query}`, "Unable to refresh leads");
  allLeads = asArray(payload && payload.leads);
  currentPage = 1;
  updateSectionTitle();
  renderLeadsTable();
}

async function loadUsers() {
  if (currentRole !== "admin") return;
  const payload = await fetchJson("/admin/staff/list", "Unable to fetch staff users");
  allUsers = asArray(payload && payload.staff);
  renderUsersTable();
}

async function refreshDashboard() {
  if (refreshInFlight) return;
  refreshInFlight = true;
  setStatus("Loading dashboard...");
  const jobs = [loadLeads()];
  if (currentRole === "admin") jobs.push(loadAnalytics(), loadUsers());

  try {
    const results = await Promise.allSettled(jobs);
    const hasFailure = results.some((result) => result.status === "rejected");
    if (hasFailure) {
      setStatus("Unable to refresh some dashboard data.", true);
      return;
    }
    renderSourceChart(allLeads);
    setStatus("Dashboard updated.");
  } finally {
    refreshInFlight = false;
  }
}

async function deleteLead(leadId) {
  if (currentRole !== "admin") return;
  if (!confirm("Delete this lead?")) return;

  await fetchJson(`/admin/leads/${leadId}`, "Unable to delete lead", {
    method: "DELETE",
  });
  await refreshDashboard();
}

async function updateLeadStatus(leadId) {
  const input = document.getElementById(`status-${leadId}`);
  const statusValue = String(input?.value || "").trim();
  if (!statusValue) {
    alert("Please enter a status value.");
    return;
  }

  await fetchJson(`/admin/leads/${leadId}/status`, "Unable to update lead status", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ working_status: statusValue }),
  });
  await refreshDashboard();
}

async function addStaffUser(event) {
  event.preventDefault();
  const nameEl = document.getElementById("new-user-name");
  const emailEl = document.getElementById("new-user-email");
  const passwordEl = document.getElementById("new-user-password");
  if (!nameEl || !emailEl || !passwordEl) return;

  const payload = {
    name: String(nameEl.value || "").trim(),
    email: String(emailEl.value || "").trim().toLowerCase(),
    password: String(passwordEl.value || "").trim(),
    role: "staff",
  };

  await fetchJson("/admin/staff/create", "Unable to create staff", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  nameEl.value = "";
  emailEl.value = "";
  passwordEl.value = "";
  await loadUsers();
}

async function activateUser(userId) {
  await fetchJson(`/admin/staff/activate/${userId}`, "Unable to activate user", {
    method: "PUT",
  });
  await loadUsers();
}

async function deactivateUser(userId) {
  await fetchJson(`/admin/staff/deactivate/${userId}`, "Unable to deactivate user", {
    method: "PUT",
  });
  await loadUsers();
}

async function setUserRole(userId, role) {
  await fetchJson(`/admin/staff/set-role/${userId}`, "Unable to change role", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  await loadUsers();
}

async function deleteUser(userId) {
  if (!confirm("Delete this user?")) return;
  await fetchJson(`/admin/staff/delete/${userId}`, "Unable to delete user", {
    method: "DELETE",
  });
  await loadUsers();
}

async function logout() {
  window.location.href = "/logout";
}

window.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form.toolbar");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await refreshDashboard();
    });
  }

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await logout();
      } catch (_error) {
        alert("Logout failed. Please try again.");
      }
    });
  }

  const addUserForm = document.getElementById("add-user-form");
  if (addUserForm) {
    addUserForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await addStaffUser(event);
      } catch (_error) {
        alert("Unable to create user.");
      }
    });
  }

  document.addEventListener("click", async (event) => {
    const deleteBtn = event.target.closest(".delete-btn");
    if (deleteBtn) {
      const leadId = Number(deleteBtn.getAttribute("data-lead-id"));
      if (leadId) {
        try {
          await deleteLead(leadId);
        } catch (_error) {
          alert("Unable to delete lead.");
        }
      }
      return;
    }

    const statusBtn = event.target.closest(".status-btn");
    if (statusBtn) {
      const leadId = Number(statusBtn.getAttribute("data-lead-id"));
      if (leadId) {
        try {
          await updateLeadStatus(leadId);
        } catch (_error) {
          alert("Unable to update lead status.");
        }
      }
      return;
    }

    const activateBtn = event.target.closest(".activate-btn");
    if (activateBtn) {
      const userId = Number(activateBtn.getAttribute("data-user-id"));
      if (userId) {
        try {
          await activateUser(userId);
        } catch (_error) {
          alert("Unable to activate user.");
        }
      }
      return;
    }

    const deactivateBtn = event.target.closest(".deactivate-btn");
    if (deactivateBtn) {
      const userId = Number(deactivateBtn.getAttribute("data-user-id"));
      if (userId) {
        try {
          await deactivateUser(userId);
        } catch (_error) {
          alert("Unable to deactivate user.");
        }
      }
      return;
    }

    const setRoleBtn = event.target.closest(".set-role-btn");
    if (setRoleBtn) {
      const userId = Number(setRoleBtn.getAttribute("data-user-id"));
      const role = String(setRoleBtn.getAttribute("data-role") || "staff").toLowerCase();
      if (userId) {
        try {
          await setUserRole(userId, role);
        } catch (_error) {
          alert("Unable to change user role.");
        }
      }
      return;
    }

    const deleteUserBtn = event.target.closest(".delete-user-btn");
    if (deleteUserBtn) {
      const userId = Number(deleteUserBtn.getAttribute("data-user-id"));
      if (userId) {
        try {
          await deleteUser(userId);
        } catch (_error) {
          alert("Unable to delete user.");
        }
      }
    }
  });

  const prevBtn = document.getElementById("prev-page");
  const nextBtn = document.getElementById("next-page");
  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (currentPage <= 1) return;
      currentPage -= 1;
      renderLeadsTable();
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      const totalPages = Math.max(1, Math.ceil(allLeads.length / pageSize));
      if (currentPage >= totalPages) return;
      currentPage += 1;
      renderLeadsTable();
    });
  }

  refreshDashboard();
  refreshTimer = setInterval(() => {
    if (!document.hidden) {
      refreshDashboard();
    }
  }, 20000);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      refreshDashboard();
    }
  });
});
