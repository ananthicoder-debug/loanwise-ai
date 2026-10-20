/* ===================================================================
   LoanWise AI — common.js  v2.0
   Shared utilities: API, auth, sidebar, formatting
=================================================================== */

/* ─── API Base URL ────────────────────────────────────────────
   LOCAL:      http://127.0.0.1:8000  (default, for local development)
   PRODUCTION: set to your deployed backend URL, e.g.:
               https://loanwise-ai-backend.onrender.com
   ─────────────────────────────────────────────────────────── */
const API_BASE_URL = window._LOANWISE_API_URL || "http://127.0.0.1:8000";

/* ─── Connection health check ────────────────────────────────── */
function checkBackendConnection() {
  fetch(API_BASE_URL + "/api/health")
    .then(r => r.json())
    .then(data => {
      if (data.mongodb === "disconnected") {
        const el = document.getElementById("backendAlert");
        if (el) el.innerHTML = `<div class="alert alert-warning alert-dismissible fade show small mb-0" role="alert">
          ⚠️ Database connection issue. Some features may not work. Start MongoDB and restart the backend.
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
      }
    })
    .catch(() => {
      const el = document.getElementById("backendAlert");
      if (el) el.innerHTML = `<div class="alert alert-danger alert-dismissible fade show small mb-0" role="alert">
        🔴 Cannot reach the backend server at <strong>http://localhost:8000</strong>.
        Please run <strong>START_LOANWISE.bat</strong> and wait for it to start, then refresh this page.
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
    });
}

/* ─── Auth token storage ─────────────────────────────────────── */
function setSession(token, role, fullName) {
  localStorage.setItem("lw_token", token);
  localStorage.setItem("lw_role", role);
  localStorage.setItem("lw_name", fullName);
}
function getToken()    { return localStorage.getItem("lw_token"); }
function getRole()     { return localStorage.getItem("lw_role"); }
function getFullName() { return localStorage.getItem("lw_name") || "User"; }
function clearSession() {
  localStorage.removeItem("lw_token");
  localStorage.removeItem("lw_role");
  localStorage.removeItem("lw_name");
}
function logout() { clearSession(); window.location.href = "login.html"; }

/* ─── Route guards ───────────────────────────────────────────── */
function requireAuth()  { if (!getToken()) { window.location.href = "login.html"; } }
function requireAdmin() { requireAuth(); if (getRole() !== "admin") { window.location.href = "dashboard.html"; } }

/* ─── AJAX wrapper ───────────────────────────────────────────── */
function laAjax(method, path, data) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  return new Promise((resolve, reject) => {
    $.ajax({
      url: API_BASE_URL + path,
      method: method,
      headers: headers,
      contentType: "application/json",
      data: (data !== undefined && data !== null) ? JSON.stringify(data) : undefined,
      dataType: "json",
    })
    .done(resolve)
    .fail(function(xhr) {
      if (xhr.status === 401) {
        clearSession();
        window.location.href = "login.html";
        return;
      }
      let message = "Unable to connect to the backend server. Make sure START_LOANWISE.bat is running.";
      if (xhr.status === 0) {
        message = "Cannot reach the backend at http://localhost:8000. Please start the backend server using START_LOANWISE.bat and refresh.";
      } else if (xhr.responseJSON && xhr.responseJSON.detail) {
        message = typeof xhr.responseJSON.detail === "string"
          ? xhr.responseJSON.detail
          : JSON.stringify(xhr.responseJSON.detail);
      }
      reject({ status: xhr.status, message });
    });
  });
}

/* ─── Alert helper ───────────────────────────────────────────── */
function showAlert(containerId, message, type = "danger") {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show mb-3" role="alert">
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  </div>`;
}

/* ─── Formatting helpers ─────────────────────────────────────── */
function formatCurrency(amount) {
  if (amount == null) return "—";
  return "₹" + Number(amount).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}
function formatPercent(val) { return val != null ? Number(val).toFixed(2) + "%" : "—"; }
function formatDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr;
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}
function statusBadgeHtml(status) {
  const cls = {
    PAID: "badge-status-paid", UPCOMING: "badge-status-upcoming",
    DUE: "badge-status-due", OVERDUE: "badge-status-overdue",
  };
  return `<span class="${cls[status] || 'badge-status-upcoming'}">${status}</span>`;
}

/* ─── Sidebar builder ────────────────────────────────────────── */
function buildSidebar(activePage) {
  const isAdmin = getRole() === "admin";
  const name = getFullName();

  let links = "";
  if (isAdmin) {
    links = `
      <div class="lw-sidebar-section">Admin</div>
      ${sidebarLink("dashboard", "admin-dashboard.html", "📊", "Dashboard", activePage)}
      ${sidebarLink("admin-users", "admin-users.html", "👥", "Users", activePage)}
      ${sidebarLink("admin-applications", "admin-applications.html", "📋", "Applications", activePage)}
      ${sidebarLink("admin-lenders", "admin-lenders.html", "🏦", "Lenders", activePage)}
      ${sidebarLink("admin-products", "admin-products.html", "📦", "Products", activePage)}
      ${sidebarLink("admin-predictions", "admin-predictions.html", "🤖", "Predictions", activePage)}
      ${sidebarLink("admin-recommendations", "admin-recommendations.html", "⭐", "Recommendations", activePage)}
      ${sidebarLink("admin-active-loans", "admin-active-loans.html", "💰", "Active Loans", activePage)}
      ${sidebarLink("admin-payments", "admin-payments.html", "💳", "Payments", activePage)}
      ${sidebarLink("admin-datasets", "admin-datasets.html", "🗄️", "Datasets", activePage)}
      ${sidebarLink("admin-data-quality", "admin-data-quality.html", "✅", "Data Quality", activePage)}
      ${sidebarLink("admin-documents", "admin-documents.html", "📁", "Doc Verification", activePage)}
      ${sidebarLink("admin-feedback", "admin-feedback.html", "💬", "Feedback", activePage)}`;
  } else {
    links = `
      <div class="lw-sidebar-section">Main</div>
      ${sidebarLink("dashboard", "dashboard.html", "🏠", "Dashboard", activePage)}
      ${sidebarLink("profile", "profile.html", "👤", "My Profile", activePage)}
      ${sidebarLink("financial-health", "financial-health.html", "📈", "Financial Profile", activePage)}
      <div class="lw-sidebar-section">Loans</div>
      ${sidebarLink("loan-categories", "loan-categories.html", "📂", "Loan Categories", activePage)}
      ${sidebarLink("lenders", "lenders.html", "🏦", "Lenders", activePage)}
      ${sidebarLink("loan-search", "loan-search.html", "🔍", "Search Loans", activePage)}
      ${sidebarLink("eligible-loans", "eligible-loans.html", "✅", "Eligible Loans", activePage)}
      ${sidebarLink("recommended-loans", "recommended-loans.html", "⭐", "Recommended", activePage)}
      ${sidebarLink("assessment-report", "assessment-report.html", "📊", "Assessment Report", activePage)}
      ${sidebarLink("compare-loans", "compare-loans.html", "⚖️", "Compare Loans", activePage)}
      ${sidebarLink("emi-calculator", "emi-calculator.html", "🧮", "EMI Calculator", activePage)}
      <div class="lw-sidebar-section">My Loans</div>
      ${sidebarLink("applications", "applications.html", "📋", "Applications", activePage)}
      ${sidebarLink("active-loans", "active-loans.html", "💰", "Active Loans", activePage)}
      ${sidebarLink("payment-history", "payment-history.html", "💳", "Payments", activePage)}
      ${sidebarLink("notifications", "notifications.html", "🔔", "Notifications", activePage)}
      ${sidebarLink("documents", "documents.html", "📁", "Documents", activePage)}
      ${sidebarLink("feedback", "feedback.html", "💬", "Feedback", activePage)}`;
  }

  const html = `
    <div class="lw-sidebar-brand">💜 LoanWise <span>AI</span></div>
    <nav class="lw-sidebar-nav">
      <ul class="nav flex-column">${links}</ul>
    </nav>
    <div class="lw-sidebar-footer">
      <div>👤 ${escapeHtml(name)}</div>
      <button class="btn btn-sm btn-la-accent mt-2 w-100" onclick="logout()">Logout</button>
    </div>`;

  const el = document.getElementById("lwSidebar");
  if (el) el.innerHTML = html;
}

function sidebarLink(key, href, icon, label, activePage) {
  const cls = activePage === key ? "nav-link active" : "nav-link";
  return `<li class="nav-item"><a class="${cls}" href="${href}"><span class="icon">${icon}</span>${label}</a></li>`;
}

/* ─── Topbar builder ─────────────────────────────────────────── */
function buildTopbar(title) {
  const el = document.getElementById("lwTopbar");
  if (!el) return;
  el.innerHTML = `
    <div class="d-flex align-items-center gap-3">
      <button class="lw-sidebar-toggle" id="sidebarToggle">☰</button>
      <span class="lw-topbar-title">${title || "LoanWise AI"}</span>
    </div>
    <div class="lw-topbar-right">
      <span class="d-none d-md-inline" style="font-size:0.88rem;color:#6B7280">👤 ${escapeHtml(getFullName())}</span>
    </div>`;

  // Insert backend-alert container after topbar if not already present
  if (!document.getElementById("backendAlert")) {
    const alertDiv = document.createElement("div");
    alertDiv.id = "backendAlert";
    alertDiv.style.cssText = "position:sticky;top:0;z-index:1050;";
    el.parentNode.insertBefore(alertDiv, el.nextSibling);
  }

  document.getElementById("sidebarToggle")?.addEventListener("click", toggleSidebar);
}

function toggleSidebar() {
  document.getElementById("lwSidebar")?.classList.toggle("open");
  document.getElementById("sidebarOverlay")?.classList.toggle("open");
}

/* ─── Legacy navbar (for auth pages without sidebar) ────────── */
function renderNavbar(activePage) {
  const isLoggedIn = !!getToken();
  const isAdmin = getRole() === "admin";
  let links = "";
  if (!isLoggedIn) {
    links = `
      <li class="nav-item"><a class="nav-link" href="index.html">Home</a></li>
      <li class="nav-item"><a class="nav-link" href="login.html">Login</a></li>
      <li class="nav-item"><a class="nav-link" href="register.html">Register</a></li>`;
  } else if (isAdmin) {
    links = `<li class="nav-item"><a class="nav-link" href="admin-dashboard.html">Admin Dashboard</a></li>`;
  } else {
    links = `<li class="nav-item"><a class="nav-link" href="dashboard.html">Dashboard</a></li>`;
  }

  const rightSide = isLoggedIn
    ? `<span id="navUserBadge" class="me-3">👤 ${escapeHtml(getFullName())}</span>
       <button class="btn btn-sm btn-la-accent" onclick="logout()">Logout</button>`
    : "";

  const html = `
    <nav class="navbar navbar-expand-lg la-navbar sticky-top">
      <div class="container">
        <a class="navbar-brand" href="index.html">💜 LoanWise <span style="color:#F97316">AI</span></a>
        <button class="navbar-toggler bg-light" type="button" data-bs-toggle="collapse" data-bs-target="#laNavContent">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="laNavContent">
          <ul class="navbar-nav me-auto">${links}</ul>
          <div class="d-flex align-items-center">${rightSide}</div>
        </div>
      </div>
    </nav>`;

  $("#laNavbar").html(html);
}

/* ─── Utility ────────────────────────────────────────────────── */
function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function getQueryParam(key) {
  return new URLSearchParams(window.location.search).get(key);
}

function initPageLayout(activePage, topbarTitle) {
  requireAuth();
  buildSidebar(activePage);
  buildTopbar(topbarTitle || activePage);
  // Mobile sidebar overlay click to close
  document.getElementById("sidebarOverlay")?.addEventListener("click", toggleSidebar);
  // Check backend is reachable
  checkBackendConnection();
  // Sync the user's name from the server (in case it was updated on another tab or page)
  _syncUserName(activePage, topbarTitle);
}

/* Silently fetch the current name from /api/auth/me and refresh if it changed */
function _syncUserName(activePage, topbarTitle) {
  const token = getToken();
  if (!token) return;
  fetch(API_BASE_URL + "/api/auth/me", {
    headers: { "Authorization": "Bearer " + token }
  })
  .then(r => r.ok ? r.json() : null)
  .then(data => {
    if (!data || !data.full_name) return;
    const stored = localStorage.getItem("lw_name");
    if (stored !== data.full_name) {
      // Name changed — update storage and redraw sidebar + topbar
      localStorage.setItem("lw_name", data.full_name);
      buildSidebar(activePage);
      buildTopbar(topbarTitle || activePage);
    }
  })
  .catch(() => {}); // silent — don't disrupt the page if this fails
}

/* ─── Product card renderer (used by multiple pages) ────────── */
function renderProductCard(product, showEligibility = true) {
  const eligBadge = showEligibility && product.eligibility_status
    ? `<span class="${product.eligibility_status === 'Potentially Eligible' ? 'badge-eligible' : 'badge-not-eligible'}">${product.eligibility_status}</span>`
    : "";
  const emiHtml = product.estimated_emi
    ? `<div class="emi-highlight mt-2">Est. EMI: ${formatCurrency(product.estimated_emi)}/mo</div>`
    : "";
  const reasonHtml = (product.rule_reasons && product.rule_reasons.length > 0 && product.eligibility_status !== "Potentially Eligible")
    ? `<div class="small text-danger mt-1">${escapeHtml(product.rule_reasons[0])}</div>` : "";
  const sourceTag = product.verification_status === "Verified"
    ? `<div class="source-tag">✅ Verified from official source • ${product.source_date || ""}</div>`
    : `<div class="source-tag">ℹ️ Source: ${escapeHtml(product.official_product_url || "Not specified")}</div>`;

  return `
    <div class="col-md-6 col-xl-4 mb-3">
      <div class="loan-product-card h-100 d-flex flex-column">
        <div class="lender-badge">🏦 ${escapeHtml(product.lender_name)}</div>
        <div class="product-name">${escapeHtml(product.product_name)}</div>
        <div class="mb-2">${eligBadge}</div>
        <div class="d-flex flex-wrap gap-2 mb-2">
          <span class="rate-badge">Rate: ${product.interest_rate_min}%–${product.interest_rate_max}%</span>
          <span class="rate-badge">Tenure: ${product.min_tenure}–${product.max_tenure} mo</span>
        </div>
        <div class="small text-muted mb-1">Amount: ${formatCurrency(product.min_amount)} – ${formatCurrency(product.max_amount)}</div>
        <div class="small text-muted mb-1">Processing Fee: ${escapeHtml(product.processing_fee || "Not specified")}</div>
        ${emiHtml}${reasonHtml}
        ${sourceTag}
        <div class="mt-auto pt-2 d-flex gap-2 flex-wrap">
          <button class="btn btn-sm btn-la-outline view-details-btn" data-id="${product._id}">Details</button>
          <button class="btn btn-sm btn-la-accent add-compare-btn" data-id="${product._id}" data-name="${escapeHtml(product.product_name)}">Compare</button>
        </div>
      </div>
    </div>`;
}
