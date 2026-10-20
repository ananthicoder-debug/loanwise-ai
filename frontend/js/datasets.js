/* ===================================================================
   LoanWise AI — datasets.js  v1.0
   Handles: Verified Products page (initVerifiedProductsPage)
=================================================================== */

let _vpAllProducts = [];

function initVerifiedProductsPage() {
  initPageLayout("loan-search", "Verified Products");
  _loadVerifiedProducts();

  // Live search on keyup
  document.getElementById("vpSearch")?.addEventListener("input", _applyVpFilters);
  document.getElementById("vpCatFilter")?.addEventListener("change", _applyVpFilters);
  document.getElementById("vpLenderFilter")?.addEventListener("change", _applyVpFilters);
}

function _loadVerifiedProducts() {
  laAjax("GET", "/api/loans")
    .then(grouped => {
      _vpAllProducts = [];
      // Flatten the grouped response (category → lenders → products)
      if (typeof grouped === "object" && !Array.isArray(grouped)) {
        Object.values(grouped).forEach(catData => {
          if (catData && catData.lenders) {
            Object.values(catData.lenders).forEach(lenderData => {
              if (lenderData && lenderData.products) {
                _vpAllProducts.push(...lenderData.products);
              }
            });
          }
        });
      } else if (Array.isArray(grouped)) {
        _vpAllProducts = grouped;
      }

      _populateVpStats();
      _populateVpFilters();
      _renderVpTable(_vpAllProducts);
    })
    .catch(err => showAlert("vpAlert", err.message, "danger"));
}

function _populateVpStats() {
  const categories = [...new Set(_vpAllProducts.map(p => p.loan_category))];
  const lenders    = [...new Set(_vpAllProducts.map(p => p.lender_name))];

  const stats = [
    { icon: "📦", value: _vpAllProducts.length, label: "Total Products" },
    { icon: "🏦", value: lenders.length,         label: "Lenders" },
    { icon: "📂", value: categories.length,      label: "Categories" },
    { icon: "✅", value: _vpAllProducts.filter(p => p.verification_status === "Verified").length, label: "Verified" },
  ];

  const statsEl = document.getElementById("vpStats");
  if (!statsEl) return;
  statsEl.innerHTML = stats.map(s => `
    <div class="col-6 col-md-3">
      <div class="la-stat-card text-center">
        <div class="stat-icon">${s.icon}</div>
        <div class="stat-value">${s.value}</div>
        <div class="stat-label">${s.label}</div>
      </div>
    </div>`).join("");
}

function _populateVpFilters() {
  const categories = [...new Set(_vpAllProducts.map(p => p.loan_category))].sort();
  const lenders    = [...new Set(_vpAllProducts.map(p => p.lender_name))].sort();

  const catSel = document.getElementById("vpCatFilter");
  if (catSel) {
    catSel.innerHTML = `<option value="">All Categories</option>` +
      categories.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
  }

  const lendSel = document.getElementById("vpLenderFilter");
  if (lendSel) {
    lendSel.innerHTML = `<option value="">All Lenders</option>` +
      lenders.map(l => `<option value="${escapeHtml(l)}">${escapeHtml(l)}</option>`).join("");
  }
}

function _applyVpFilters() {
  const q    = (document.getElementById("vpSearch")?.value || "").toLowerCase().trim();
  const cat  = document.getElementById("vpCatFilter")?.value || "";
  const lend = document.getElementById("vpLenderFilter")?.value || "";

  const filtered = _vpAllProducts.filter(p => {
    const matchQ = !q
      || (p.product_name || "").toLowerCase().includes(q)
      || (p.lender_name  || "").toLowerCase().includes(q);
    const matchC = !cat  || p.loan_category === cat;
    const matchL = !lend || p.lender_name   === lend;
    return matchQ && matchC && matchL;
  });

  _renderVpTable(filtered);
}

function _renderVpTable(products) {
  const tbody = document.getElementById("vpTableBody");
  if (!tbody) return;

  if (!products.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No products match this filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = products.map(p => `
    <tr>
      <td class="fw-bold small">${escapeHtml(p.lender_name)}</td>
      <td class="small">${escapeHtml(p.product_name)}</td>
      <td class="small">${escapeHtml(p.loan_category)}</td>
      <td class="small">${formatCurrency(p.min_amount)} – ${formatCurrency(p.max_amount)}</td>
      <td class="small">${p.interest_rate_min}%–${p.interest_rate_max}%</td>
      <td class="small">${p.min_tenure}–${p.max_tenure} mo</td>
      <td>
        <span class="badge-verified">${escapeHtml(p.verification_status || "Verified")}</span>
      </td>
      <td class="small text-muted">${escapeHtml(p.source_date || "—")}</td>
      <td class="text-nowrap">
        ${p.official_product_url
          ? `<a href="${p.official_product_url}" target="_blank" class="btn btn-sm btn-la-outline me-1">Official ↗</a>`
          : ""}
        <a href="loan-details.html?product_id=${p._id}" class="btn btn-sm btn-la-primary">Details</a>
      </td>
    </tr>`).join("");
}
