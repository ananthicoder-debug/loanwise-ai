/* ===================================================================
   LoanWise AI — payments.js
   Handles: EMI Schedule, Payment History
=================================================================== */

/* ─── EMI Schedule Page ──────────────────────────────────────── */
function initEmiSchedulePage() {
  initPageLayout("active-loans", "EMI Schedule");
  const loanId = getQueryParam("loan_id");
  if (!loanId) {
    showAlert("scheduleAlert", "No loan selected. <a href='active-loans.html'>Go to Active Loans</a>.", "warning");
    return;
  }

  // Load loan details first
  laAjax("GET", `/api/active-loans/${loanId}`)
    .then(loan => renderLoanSummary(loan))
    .catch(() => {});

  // Load schedule
  laAjax("GET", `/api/active-loans/${loanId}/payments`)
    .then(payments => renderSchedule(payments, loanId))
    .catch(err => showAlert("scheduleAlert", err.message, "danger"));
}

function renderLoanSummary(loan) {
  const cards = document.getElementById("loanSummaryCards");
  if (!cards) return;
  cards.innerHTML = `
    <div class="col-6 col-md-3"><div class="la-stat-card"><div class="stat-value">${formatCurrency(loan.actual_amount)}</div><div class="stat-label">Loan Amount</div></div></div>
    <div class="col-6 col-md-3"><div class="la-stat-card orange"><div class="stat-value">${formatCurrency(loan.emi_amount)}</div><div class="stat-label">Monthly EMI</div></div></div>
    <div class="col-6 col-md-3"><div class="la-stat-card green"><div class="stat-value">${loan.interest_rate}%</div><div class="stat-label">Interest Rate</div></div></div>
    <div class="col-6 col-md-3"><div class="la-stat-card navy"><div class="stat-value">${loan.tenure_months} mo</div><div class="stat-label">Tenure</div></div></div>`;
}

function renderSchedule(payments, loanId) {
  const tbody = document.getElementById("scheduleBody");
  if (!payments.length) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-muted">No payment schedule found.</td></tr>`;
    return;
  }

  let html = "";
  payments.forEach(p => {
    const rowClass = p.payment_status === "OVERDUE" ? "emi-row overdue"
      : p.payment_status === "DUE" ? "emi-row due"
      : p.payment_status === "PAID" ? "emi-row paid"
      : "emi-row upcoming";

    const canPay = p.payment_status !== "PAID";
    html += `<tr class="${rowClass}">
      <td>${p.emi_number}</td>
      <td>${formatDate(p.due_date)}</td>
      <td class="fw-bold">${formatCurrency(p.amount_due)}</td>
      <td class="small">${formatCurrency(p.principal_component)}</td>
      <td class="small">${formatCurrency(p.interest_component)}</td>
      <td>${statusBadgeHtml(p.payment_status)}</td>
      <td class="small">${p.payment_date ? formatDate(p.payment_date) : "—"}</td>
      <td class="small">${p.days_overdue > 0 ? `<span class="text-danger">${p.days_overdue}</span>` : "0"}</td>
      <td class="small">${p.late_charge > 0 ? `<span class="text-danger">${formatCurrency(p.late_charge)}</span>` : "—"}</td>
      <td>${canPay ? `<button class="btn btn-sm btn-la-primary" onclick="markPaid('${p._id}', ${p.amount_due})">Mark Paid</button>` : "✅"}</td>
    </tr>`;
  });
  tbody.innerHTML = html;
}

function markPaid(paymentId, amountDue) {
  if (!confirm(`Mark this EMI of ${formatCurrency(amountDue)} as paid?`)) return;
  laAjax("POST", `/api/payments/${paymentId}/mark-paid`, { amount_paid: amountDue })
    .then(() => {
      const loanId = getQueryParam("loan_id");
      laAjax("GET", `/api/active-loans/${loanId}/payments`)
        .then(payments => renderSchedule(payments, loanId));
    })
    .catch(err => showAlert("scheduleAlert", err.message, "danger"));
}

/* ─── Payment History Page ───────────────────────────────────── */
function initPaymentHistoryPage() {
  initPageLayout("payment-history", "Payment History");
  const loanId = getQueryParam("loan_id");

  if (loanId) {
    laAjax("GET", `/api/active-loans/${loanId}/payments`)
      .then(payments => renderPaymentHistory(payments))
      .catch(err => showAlert("paymentHistAlert", err.message, "danger"));
  } else {
    loadAllPayments();
  }

  // Filters
  document.getElementById("filterStatus")?.addEventListener("change", filterPayments);
  document.getElementById("filterLoan")?.addEventListener("change", filterPayments);
}

let allPayments = [];

function loadAllPayments() {
  // Load all active loans first, then their payments
  laAjax("GET", "/api/active-loans")
    .then(loans => {
      if (!loans.length) {
        renderPaymentHistory([]);
        return;
      }
      const loanSelect = document.getElementById("filterLoan");
      if (loanSelect) {
        loanSelect.innerHTML = `<option value="">All Loans</option>`;
        loans.forEach(l => {
          loanSelect.innerHTML += `<option value="${l._id}">${escapeHtml(l.product_name)} — ${formatCurrency(l.actual_amount)}</option>`;
        });
      }
      // Load payments for first loan (or all)
      const firstLoanId = loans[0]._id;
      return laAjax("GET", `/api/active-loans/${firstLoanId}/payments`);
    })
    .then(payments => { if (payments) renderPaymentHistory(payments); })
    .catch(err => showAlert("paymentHistAlert", err.message, "danger"));
}

function renderPaymentHistory(payments) {
  allPayments = payments;
  applyPaymentFilter(payments);
}

function filterPayments() {
  const statusFilter = document.getElementById("filterStatus")?.value || "";
  const filtered = statusFilter
    ? allPayments.filter(p => p.payment_status === statusFilter)
    : allPayments;
  applyPaymentFilter(filtered);
}

function applyPaymentFilter(payments) {
  const tbody = document.getElementById("paymentHistBody");
  if (!tbody) return;
  if (!payments.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">No payment records found.</td></tr>`;
    return;
  }

  // Summary counts
  const counts = { PAID: 0, DUE: 0, OVERDUE: 0, UPCOMING: 0 };
  payments.forEach(p => { if (counts[p.payment_status] !== undefined) counts[p.payment_status]++; });
  const summaryEl = document.getElementById("paymentSummary");
  if (summaryEl) {
    summaryEl.innerHTML = Object.entries(counts)
      .map(([s, c]) => `<span class="me-3">${statusBadgeHtml(s)} ${c}</span>`).join("");
  }

  let html = "";
  payments.slice().reverse().forEach(p => {
    const rowClass = p.payment_status === "OVERDUE" ? "emi-row overdue"
      : p.payment_status === "DUE" ? "emi-row due"
      : p.payment_status === "PAID" ? "emi-row paid" : "emi-row";
    html += `<tr class="${rowClass}">
      <td>${p.emi_number}</td>
      <td>${formatDate(p.due_date)}</td>
      <td class="fw-bold">${formatCurrency(p.amount_due)}</td>
      <td>${formatCurrency(p.amount_paid > 0 ? p.amount_paid : null)}</td>
      <td>${statusBadgeHtml(p.payment_status)}</td>
      <td>${p.payment_date ? formatDate(p.payment_date) : "—"}</td>
      <td>${p.days_overdue > 0 ? `<span class="text-danger">${p.days_overdue} days</span>` : "—"}</td>
      <td>${p.late_charge > 0 ? `<span class="text-danger">${formatCurrency(p.late_charge)}</span>` : "—"}</td>
    </tr>`;
  });
  tbody.innerHTML = html;
}
