/* ===================================================================
   LoanWise AI — notifications.js  v1.0
   Handles: Notifications, Applications, Documents, Feedback pages
=================================================================== */

/* ─── Notifications Page ─────────────────────────────────────── */
function initNotificationsPage() {
  initPageLayout("notifications", "Notifications");
  _loadNotifications();

  document.getElementById("markAllReadBtn")?.addEventListener("click", () => {
    laAjax("PUT", "/api/notifications/read-all")
      .then(() => _loadNotifications())
      .catch(err => showAlert("notifAlert", err.message, "danger"));
  });
}

function _loadNotifications() {
  laAjax("GET", "/api/notifications")
    .then(data => _renderNotifications(data))
    .catch(err => showAlert("notifAlert", err.message, "danger"));
}

function _renderNotifications(data) {
  const emiNotifs = data.emi_notifications    || [];
  const sysNotifs = data.system_notifications || [];
  let html = "";

  if (emiNotifs.length) {
    html += `<div class="la-card mb-4">
      <div class="la-card-header">📅 EMI Reminders &amp; Alerts (${emiNotifs.length})</div>`;
    emiNotifs.forEach(n => {
      const cls  = n.type === "overdue" ? "overdue" : "upcoming";
      const icon = n.type === "overdue" ? "⚠️" : "📅";
      html += `<div class="notification-item ${cls} mb-2">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <div class="fw-bold small">${icon} ${n.type === "overdue" ? "Overdue EMI" : "Upcoming EMI"}</div>
            <div class="small mt-1">${escapeHtml(n.message)}</div>
            <div class="small text-muted mt-1">Due: ${formatDate(n.due_date)} | Amount: ${formatCurrency(n.amount_due)}</div>
            ${n.estimated_late_charge > 0
              ? `<div class="small text-danger mt-1">Est. Late Charge: ${formatCurrency(n.estimated_late_charge)}</div>`
              : ""}
          </div>
          ${n.active_loan_id
            ? `<a href="emi-schedule.html?loan_id=${n.active_loan_id}" class="btn btn-sm btn-la-outline ms-3">View Schedule</a>`
            : ""}
        </div>
      </div>`;
    });
    html += "</div>";
  }

  if (sysNotifs.length) {
    html += `<div class="la-card mb-4">
      <div class="la-card-header">🔔 System Notifications (${sysNotifs.length})</div>`;
    sysNotifs.forEach(n => {
      const unread = !n.is_read;
      html += `<div class="notification-item system mb-2${n.is_read ? " opacity-75" : ""}">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <div class="fw-bold small">${unread ? "🔵 " : ""}${escapeHtml(n.title || n.type || "Notification")}</div>
            <div class="small mt-1">${escapeHtml(n.message || "")}</div>
            <div class="small text-muted mt-1">${formatDate(n.created_at)}</div>
          </div>
          ${unread
            ? `<button class="btn btn-sm btn-la-ghost ms-3" onclick="markNotifRead('${n._id}')">Mark Read</button>`
            : `<span class="small text-muted">Read ✓</span>`}
        </div>
      </div>`;
    });
    html += "</div>";
  }

  if (!emiNotifs.length && !sysNotifs.length) {
    html = `<div class="empty-state">
      <div class="empty-icon">🔔</div>
      <div class="empty-msg">No notifications.</div>
      <div class="empty-sub">EMI reminders will appear here once you have active loans.</div>
    </div>`;
  }

  document.getElementById("notifContent").innerHTML = html;
}

function markNotifRead(id) {
  laAjax("PUT", `/api/notifications/${id}/read`)
    .then(() => _loadNotifications())
    .catch(() => {});
}

/* ─── Applications Page ──────────────────────────────────────── */
function initApplicationsPage() {
  initPageLayout("applications", "My Applications");
  laAjax("GET", "/api/applications")
    .then(apps => {
      if (!apps || !apps.length) {
        document.getElementById("appsContent").innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">📋</div>
            <div class="empty-msg">No applications yet.</div>
            <div class="empty-sub">
              <a href="eligible-loans.html">Check eligibility</a> to create your first application.
            </div>
          </div>`;
        return;
      }

      const ICONS = {
        "Personal Loan": "💳", "Home Loan": "🏠", "Vehicle Loan": "🚗",
        "Education Loan": "🎓", "Gold Loan": "🪙", "Business Loan": "💼",
        "Consumer Durable Loan": "📺",
      };

      let html = `<div class="la-card">
        <div class="table-responsive">
          <table class="lw-table">
            <thead>
              <tr>
                <th>App ID</th><th>Category</th><th>Amount</th><th>Tenure</th>
                <th>Purpose</th><th>Date</th><th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>`;
      apps.forEach(app => {
        const icon = ICONS[app.loan_category] || "📋";
        html += `<tr>
          <td class="small text-muted">${app._id.slice(-8).toUpperCase()}</td>
          <td>${icon} ${escapeHtml(app.loan_category)}</td>
          <td class="fw-bold">${formatCurrency(app.loan_amount)}</td>
          <td>${app.loan_tenure} mo</td>
          <td class="small text-muted">${escapeHtml(app.purpose || "—")}</td>
          <td class="small">${formatDate(app.application_date)}</td>
          <td><span class="badge-eligible">${escapeHtml(app.status || "evaluated")}</span></td>
          <td>
            <a href="eligible-loans.html"
               onclick="sessionStorage.setItem('lw_last_app_id','${app._id}')"
               class="btn btn-sm btn-la-primary">View Results</a>
          </td>
        </tr>`;
      });
      html += "</tbody></table></div></div>";
      document.getElementById("appsContent").innerHTML = html;
    })
    .catch(err => showAlert("appsAlert", err.message, "danger"));
}

/* ─── Documents Page (legacy handler — superseded by documents.js) ─── */
function _initDocumentsPageLegacy() {
  initPageLayout("documents", "Documents");
  _loadDocuments();

  document.getElementById("addDocForm")?.addEventListener("submit", e => {
    e.preventDefault();
    const document_type = document.getElementById("docType")?.value;
    const file_name     = (document.getElementById("docFileName") || document.getElementById("docName"))?.value.trim();
    const notes         = document.getElementById("docNotes")?.value.trim();

    if (!file_name) { showAlert("docsAlert", "Enter a file name or reference.", "warning"); return; }

    laAjax("POST", "/api/documents", { document_type, file_name, notes: notes || "" })
      .then(() => {
        document.getElementById("addDocForm").reset();
        _loadDocuments();
        showAlert("docsAlert", "Document entry added.", "success");
      })
      .catch(err => showAlert("docsAlert", err.message, "danger"));
  });
}

function _loadDocuments() {
  const listEl = document.getElementById("docsList") || document.getElementById("docList");
  if (!listEl) return;

  laAjax("GET", "/api/documents")
    .then(docs => {
      if (!docs || !docs.length) {
        listEl.innerHTML = `<div class="empty-state small">
          <div class="empty-icon">📁</div>
          <div class="empty-msg">No documents added yet.</div>
        </div>`;
        return;
      }

      const ICONS = {
        "Identity Proof": "🪪", "Address Proof": "🏠", "Income Proof": "💰",
        "Bank Statement": "🏦", "Employment Proof": "💼", "Property Documents": "📜",
        "Property Document": "📜", "Education Certificate": "🎓", "Other": "📄",
      };
      const STATUS_CLS = {
        "Verified": "badge-status-paid",
        "Pending Review": "badge-status-due",
        "Rejected": "badge-status-overdue",
      };

      listEl.innerHTML = docs.map(d => `
        <div class="doc-card justify-content-between">
          <div class="d-flex align-items-center gap-3">
            <div class="doc-icon">${ICONS[d.document_type] || "📄"}</div>
            <div>
              <div class="doc-name">${escapeHtml(d.document_type)}</div>
              <div class="doc-meta">${escapeHtml(d.file_name)} • Added ${formatDate(d.upload_date)}</div>
              ${d.notes ? `<div class="doc-meta text-muted">${escapeHtml(d.notes)}</div>` : ""}
            </div>
          </div>
          <div class="d-flex align-items-center gap-2">
            <span class="${STATUS_CLS[d.verification_status] || 'badge-status-upcoming'}">
              ${escapeHtml(d.verification_status || "Pending")}
            </span>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteDoc('${d._id}')">🗑</button>
          </div>
        </div>`).join("");
    })
    .catch(err => showAlert("docsAlert", err.message, "danger"));
}

function deleteDoc(id) {
  if (!confirm("Remove this document entry?")) return;
  laAjax("DELETE", `/api/documents/${id}`)
    .then(() => _loadDocuments())
    .catch(err => showAlert("docsAlert", err.message, "danger"));
}

/* ─── Feedback Page ──────────────────────────────────────────── */
function initFeedbackPage() {
  initPageLayout("feedback", "Feedback");
  _loadMyFeedback();

  let selectedRating = 0;

  // Handle both inline onclick (existing page) and JS-attached star buttons
  document.querySelectorAll(".star-btn").forEach(star => {
    star.addEventListener("click", () => {
      selectedRating = parseInt(star.dataset.val);
      _applyStarRating(selectedRating);
    });
  });

  // Global function for pages using onclick="setRating(n)"
  window.setRating = function(val) {
    selectedRating = val;
    _applyStarRating(val);
    const hidden = document.getElementById("ratingValue") || document.getElementById("ratingVal");
    if (hidden) hidden.value = val;
  };

  document.getElementById("feedbackForm")?.addEventListener("submit", e => {
    e.preventDefault();
    const hidden = document.getElementById("ratingValue") || document.getElementById("ratingVal");
    const rating = selectedRating || parseInt(hidden?.value || "0");
    if (!rating) { showAlert("fbAlert", "Please select a rating.", "warning"); return; }

    laAjax("POST", "/api/feedback", {
      rating,
      category: document.getElementById("fbCategory")?.value || "General",
      comments: document.getElementById("fbComments")?.value.trim() || "",
    })
    .then(() => {
      showAlert("fbAlert", "Thank you for your feedback!", "success");
      document.getElementById("feedbackForm").reset();
      selectedRating = 0;
      // Reset stars
      document.querySelectorAll(".star-btn").forEach(s => s.textContent = "⭐");
      document.querySelectorAll("#starRating span").forEach(s => s.style.opacity = "1");
      _loadMyFeedback();
    })
    .catch(err => showAlert("fbAlert", err.message, "danger"));
  });
}

function _applyStarRating(val) {
  // .star-btn style
  document.querySelectorAll(".star-btn").forEach((s, i) => {
    s.textContent = i < val ? "⭐" : "☆";
  });
  // inline opacity style
  document.querySelectorAll("#starRating span").forEach((s, i) => {
    s.style.opacity = i < val ? "1" : "0.3";
  });
  const ratingText = document.getElementById("ratingText");
  if (ratingText) {
    ratingText.textContent = ["", "Poor", "Fair", "Good", "Very Good", "Excellent"][val] || "";
  }
}

function _loadMyFeedback() {
  const el = document.getElementById("myFeedback");
  if (!el) return;
  laAjax("GET", "/api/feedback")
    .then(items => {
      if (!items || !items.length) {
        el.innerHTML = `<div class="empty-state small"><div>No feedback submitted yet.</div></div>`;
        return;
      }
      el.innerHTML = items.map(f => `
        <div class="la-card mb-2" style="background:var(--lavender)">
          <div class="d-flex justify-content-between">
            <span class="fw-bold small">${escapeHtml(f.category || "General")}</span>
            <span class="small text-muted">${formatDate(f.created_at)}</span>
          </div>
          <div>${"⭐".repeat(f.rating || 1)}</div>
          ${f.comments ? `<div class="small mt-1 text-muted">${escapeHtml(f.comments)}</div>` : ""}
        </div>`).join("");
    })
    .catch(() => {});
}
