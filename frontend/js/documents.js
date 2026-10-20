/* ===================================================================
   LoanWise AI — documents.js  v2.0
   Handles: Document upload (real files), metadata reference, list,
            download, delete; Admin verification management.
=================================================================== */

const DOC_TYPE_ICONS = {
  "Identity Proof":       "🪪",
  "Address Proof":        "🏠",
  "Income Proof":         "💰",
  "Bank Statement":       "🏦",
  "Employment Proof":     "💼",
  "Property Document":    "📜",
  "Education Certificate":"🎓",
  "Other":                "📄",
};
const STATUS_CLS = {
  "Verified":       "badge-status-paid",
  "Pending Review": "badge-status-upcoming",
  "Rejected":       "badge-status-overdue",
};

/* ─── User Documents Page ────────────────────────────────────── */
function initDocumentsPage() {
  initPageLayout("documents", "Documents");
  _loadDocuments();
  _setupUploadZone();
  _setupUploadForm();
  _setupMetadataForm();
}

function _setupUploadZone() {
  const zone  = document.getElementById("uploadZone");
  const input = document.getElementById("fileInput");
  if (!zone || !input) return;

  input.addEventListener("change", () => _previewFile(input.files[0]));

  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) { input.files = e.dataTransfer.files; _previewFile(file); }
  });
}

function _previewFile(file) {
  if (!file) return;
  const previewEl = document.getElementById("filePreview");
  const sizeMB    = (file.size / (1024 * 1024)).toFixed(2);
  if (file.size > 10 * 1024 * 1024) {
    if (previewEl) previewEl.innerHTML = `<span class="text-danger">⚠️ File is ${sizeMB} MB — exceeds 10 MB limit.</span>`;
    return;
  }
  if (previewEl) {
    previewEl.innerHTML = `✅ Selected: <strong>${escapeHtml(file.name)}</strong> (${sizeMB} MB)`;
  }
  document.querySelector(".upload-zone .upload-icon").textContent = "📎";
}

function _setupUploadForm() {
  document.getElementById("uploadDocForm")?.addEventListener("submit", async e => {
    e.preventDefault();
    const docType = document.getElementById("docType")?.value;
    const file    = document.getElementById("fileInput")?.files[0];
    const notes   = document.getElementById("docNotes")?.value.trim() || "";

    if (!docType) { showAlert("docsAlert", "Select a document type.", "warning"); return; }
    if (!file)    { showAlert("docsAlert", "Select a file to upload.", "warning"); return; }

    const progressEl = document.getElementById("uploadProgress");
    const btn        = document.getElementById("uploadBtn");
    progressEl?.classList.remove("d-none");
    btn.disabled = true;
    btn.textContent = "Uploading…";

    const formData = new FormData();
    formData.append("document_type", docType);
    formData.append("notes", notes);
    formData.append("file", file);

    try {
      const resp = await fetch(API_BASE_URL + "/api/documents/upload", {
        method: "POST",
        headers: { "Authorization": "Bearer " + getToken() },
        body: formData,
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Upload failed.");
      }
      document.getElementById("uploadDocForm").reset();
      document.getElementById("filePreview").textContent = "";
      document.querySelector(".upload-zone .upload-icon").textContent = "📁";
      showAlert("docsAlert", "✅ Document uploaded and pending admin verification.", "success");
      _loadDocuments();
    } catch (err) {
      showAlert("docsAlert", `Upload error: ${err.message}`, "danger");
    } finally {
      progressEl?.classList.add("d-none");
      btn.disabled = false;
      btn.textContent = "📤 Upload Document";
    }
  });
}

function _setupMetadataForm() {
  document.getElementById("addDocForm")?.addEventListener("submit", e => {
    e.preventDefault();
    const document_type = document.getElementById("metaDocType")?.value || "Other";
    const file_name     = document.getElementById("docFileName")?.value.trim();
    const notes         = document.getElementById("metaNotes")?.value.trim() || "";

    if (!file_name) { showAlert("docsAlert", "Enter a file name reference.", "warning"); return; }

    laAjax("POST", "/api/documents", { document_type, file_name, notes })
      .then(() => {
        document.getElementById("addDocForm").reset();
        _loadDocuments();
        showAlert("docsAlert", "Reference entry added.", "success");
      })
      .catch(err => showAlert("docsAlert", err.message, "danger"));
  });
}

function _loadDocuments() {
  const listEl = document.getElementById("docsList");
  if (!listEl) return;

  laAjax("GET", "/api/documents")
    .then(docs => {
      const countEl = document.getElementById("docCount");
      if (countEl) countEl.textContent = `— ${docs.length} document(s)`;

      if (!docs || !docs.length) {
        listEl.innerHTML = `<div class="empty-state small">
          <div class="empty-icon">📁</div>
          <div class="empty-msg">No documents uploaded yet.</div>
          <div class="empty-sub">Upload government-issued documents for admin verification.</div>
        </div>`;
        return;
      }

      listEl.innerHTML = docs.map(d => _docCardHtml(d)).join("");
    })
    .catch(err => showAlert("docsAlert", err.message, "danger"));
}

function _docCardHtml(d) {
  const icon      = DOC_TYPE_ICONS[d.document_type] || "📄";
  const statusCls = STATUS_CLS[d.verification_status] || "badge-status-upcoming";
  const isFile    = !!d.stored_filename || !!d.download_url;
  const sizeStr   = d.file_size_kb ? `${d.file_size_kb} KB • ` : "";

  const downloadBtn = isFile
    ? `<a href="${API_BASE_URL}/api/documents/${d._id}/download"
          class="btn btn-sm btn-la-outline"
          target="_blank"
          rel="noopener"
          title="Download">⬇️</a>`
    : "";
  const adminNotes = d.admin_notes
    ? `<div class="doc-meta text-muted mt-1">Admin note: ${escapeHtml(d.admin_notes)}</div>` : "";

  return `<div class="doc-card">
    <div class="doc-icon-wrap">${icon}</div>
    <div class="doc-info">
      <div class="doc-name">${escapeHtml(d.document_type)}</div>
      <div class="doc-meta">${escapeHtml(d.file_name)} • ${sizeStr}Added ${formatDate(d.upload_date)}</div>
      ${d.notes ? `<div class="doc-meta text-muted">${escapeHtml(d.notes)}</div>` : ""}
      ${adminNotes}
      ${d.verified_at ? `<div class="doc-meta text-muted">Verified: ${formatDate(d.verified_at)}</div>` : ""}
    </div>
    <div class="doc-actions">
      <span class="${statusCls}">${escapeHtml(d.verification_status || "Pending")}</span>
      ${downloadBtn}
      <button class="btn btn-sm btn-outline-danger" onclick="deleteDoc('${d._id}')">🗑</button>
    </div>
  </div>`;
}

function deleteDoc(id) {
  if (!confirm("Remove this document entry?")) return;
  laAjax("DELETE", `/api/documents/${id}`)
    .then(() => {
      _loadDocuments();
      showAlert("docsAlert", "Document removed.", "success");
    })
    .catch(err => showAlert("docsAlert", err.message, "danger"));
}


/* ─── Admin Documents Page ───────────────────────────────────── */
function initAdminDocumentsPage() {
  requireAdmin();
  buildSidebar("admin-documents");
  buildTopbar("Document Verification");
  document.getElementById("sidebarOverlay")?.addEventListener("click", toggleSidebar);
  _loadAdminDocuments();
}

function _loadAdminDocuments() {
  const el = document.getElementById("adminDocsList");
  if (!el) return;
  el.innerHTML = `<div class="text-center py-4"><span class="spinner-border spinner-la"></span></div>`;

  laAjax("GET", "/api/admin/documents")
    .then(docs => {
      // Summary badges
      const total     = docs.length;
      const pending   = docs.filter(d => d.verification_status === "Pending Review").length;
      const verified  = docs.filter(d => d.verification_status === "Verified").length;
      const rejected  = docs.filter(d => d.verification_status === "Rejected").length;
      const summEl    = document.getElementById("adminDocSummary");
      if (summEl) summEl.innerHTML = `
        <div class="row g-2 mb-4">
          <div class="col-6 col-md-3"><div class="la-card text-center"><div class="fw-bold" style="font-size:1.5rem">${total}</div><div class="small text-muted">Total</div></div></div>
          <div class="col-6 col-md-3"><div class="la-card text-center"><div class="fw-bold text-warning" style="font-size:1.5rem">${pending}</div><div class="small text-muted">Pending</div></div></div>
          <div class="col-6 col-md-3"><div class="la-card text-center"><div class="fw-bold text-success" style="font-size:1.5rem">${verified}</div><div class="small text-muted">Verified</div></div></div>
          <div class="col-6 col-md-3"><div class="la-card text-center"><div class="fw-bold text-danger" style="font-size:1.5rem">${rejected}</div><div class="small text-muted">Rejected</div></div></div>
        </div>`;

      if (!docs.length) {
        el.innerHTML = `<div class="empty-state small"><div class="empty-icon">📁</div><div class="empty-msg">No documents uploaded by users yet.</div></div>`;
        return;
      }

      // Filter tabs
      const filterEl = document.getElementById("docFilterStatus");
      const filter   = filterEl?.value || "all";
      const filtered = filter === "all" ? docs : docs.filter(d => d.verification_status === filter);

      el.innerHTML = filtered.map(d => _adminDocCard(d)).join("");
    })
    .catch(err => showAlert("adminDocsAlert", err.message, "danger"));
}

function _adminDocCard(d) {
  const icon       = DOC_TYPE_ICONS[d.document_type] || "📄";
  const statusCls  = STATUS_CLS[d.verification_status] || "badge-status-upcoming";
  const isFile     = !!d.admin_download_url;
  const sizeStr    = d.file_size_kb ? `${d.file_size_kb} KB • ` : "Metadata only • ";

  const downloadBtn = isFile
    ? `<a href="${API_BASE_URL}${d.admin_download_url}" class="btn btn-sm btn-la-outline" target="_blank" rel="noopener">⬇️ Download</a>`
    : `<span class="small text-muted">No file stored</span>`;

  return `<div class="doc-card flex-column align-items-start">
    <div class="d-flex w-100 gap-3 align-items-start">
      <div class="doc-icon-wrap">${icon}</div>
      <div class="doc-info flex-1">
        <div class="doc-name">${escapeHtml(d.document_type)}</div>
        <div class="doc-meta">User: <strong>${escapeHtml(d.user_name || "—")}</strong></div>
        <div class="doc-meta">${escapeHtml(d.file_name)} • ${sizeStr}Uploaded ${formatDate(d.upload_date)}</div>
        ${d.notes ? `<div class="doc-meta text-muted">${escapeHtml(d.notes)}</div>` : ""}
        ${d.admin_notes ? `<div class="doc-meta text-primary">Admin note: ${escapeHtml(d.admin_notes)}</div>` : ""}
        ${d.verified_by ? `<div class="doc-meta text-muted">By: ${escapeHtml(d.verified_by)} on ${formatDate(d.verified_at)}</div>` : ""}
      </div>
      <div class="doc-actions flex-column align-items-end gap-2">
        <span class="${statusCls}">${escapeHtml(d.verification_status)}</span>
        ${downloadBtn}
      </div>
    </div>

    <!-- Admin actions -->
    <div class="w-100 mt-3 p-3 bg-light rounded">
      <div class="row g-2 align-items-center">
        <div class="col-md-5">
          <input type="text" class="form-control form-control-sm" id="notes_${d._id}"
            placeholder="Admin notes (optional)" value="${escapeHtml(d.admin_notes || "")}">
        </div>
        <div class="col-md-7 d-flex gap-2 flex-wrap">
          <button class="btn btn-sm btn-success" onclick="verifyDoc('${d._id}','Verified')">✅ Verify</button>
          <button class="btn btn-sm btn-danger"  onclick="verifyDoc('${d._id}','Rejected')">❌ Reject</button>
          <button class="btn btn-sm btn-la-outline" onclick="verifyDoc('${d._id}','Pending Review')">🔄 Reset</button>
        </div>
      </div>
    </div>
  </div>`;
}

function verifyDoc(docId, status) {
  const adminNotes = document.getElementById(`notes_${docId}`)?.value.trim() || "";
  laAjax("PUT", `/api/admin/documents/${docId}/verify`, {
    verification_status: status,
    admin_notes: adminNotes,
  })
  .then(() => {
    showAlert("adminDocsAlert", `Document marked as ${status}.`, "success");
    _loadAdminDocuments();
  })
  .catch(err => showAlert("adminDocsAlert", err.message, "danger"));
}
