/* ===================================================================
   LoanWise AI — profile.js
=================================================================== */

function initProfilePage() {
  initPageLayout("profile", "My Profile");

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".lw-tab-pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab)?.classList.add("active");
    });
  });

  loadProfile();
  loadCreditProfile();
  bindForms();
}

function loadProfile() {
  laAjax("GET", "/api/users/profile")
    .then(user => {
      document.getElementById("fullName").value = user.full_name || "";
      document.getElementById("emailDisplay").value = user.email || "";
      document.getElementById("phone").value = user.phone || "";
      document.getElementById("dob").value = user.date_of_birth || "";
      document.getElementById("gender").value = user.gender || "";
      if (user.address) {
        document.getElementById("street").value = user.address.street || "";
        document.getElementById("city").value = user.address.city || "";
        document.getElementById("state").value = user.address.state || "";
        document.getElementById("pincode").value = user.address.pincode || "";
      }
    })
    .catch(err => showAlert("profileAlert", err.message, "danger"));
}

function loadCreditProfile() {
  laAjax("GET", "/api/credit-profile")
    .then(cp => {
      if (!cp || !Object.keys(cp).length) return;
      // Employment tab
      setVal("empType", cp.employment_type);
      setVal("empCategory", cp.employer_category);
      setVal("yearsEmp", cp.years_of_employment);
      setVal("education", cp.education);
      // Financial tab
      setVal("monthlyIncome", cp.monthly_income);
      setVal("annualIncome", cp.annual_income);
      setVal("dependents", cp.dependents);
      setVal("residenceType", cp.residence_type);
      setVal("existingLoans", cp.existing_loans);
      setVal("existingEmi", cp.existing_emi || cp.current_emi);
      setVal("outstandingDebt", cp.outstanding_debt);
      setVal("ccOutstanding", cp.credit_card_outstanding);
      setVal("coapplicant", cp.coapplicant ? "true" : "false");
      setVal("coapplicantIncome", cp.coapplicant_income);
      // Credit tab
      setVal("age", cp.age);
      setVal("cibilScore", cp.cibil_score);
      setVal("prevLoans", cp.previous_loans);
      setVal("missedPayments", cp.missed_payments);
      setVal("latePayments", cp.late_payments);
      setVal("avgDaysLate", cp.average_days_late);
    })
    .catch(() => {});
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el && val !== undefined && val !== null) el.value = val;
}

function bindForms() {
  document.getElementById("personalForm")?.addEventListener("submit", e => {
    e.preventDefault();
    const newName = document.getElementById("fullName").value.trim();
    laAjax("PUT", "/api/users/profile", {
      full_name: newName,
      phone: document.getElementById("phone").value.trim(),
      date_of_birth: document.getElementById("dob").value,
      gender: document.getElementById("gender").value,
      address: {
        street: document.getElementById("street").value.trim(),
        city: document.getElementById("city").value.trim(),
        state: document.getElementById("state").value,
        pincode: document.getElementById("pincode").value.trim(),
      }
    })
    .then(() => {
      // Update localStorage so sidebar, topbar, and all pages reflect the new name immediately
      localStorage.setItem("lw_name", newName);
      // Rebuild sidebar and topbar with new name
      buildSidebar("profile");
      buildTopbar("My Profile");
      showAlert("profileAlert", "Personal information saved successfully.", "success");
    })
    .catch(err => showAlert("profileAlert", err.message, "danger"));
  });

  document.getElementById("employmentForm")?.addEventListener("submit", e => {
    e.preventDefault();
    saveCreditProfile({
      employment_type: document.getElementById("empType").value,
      employer_category: document.getElementById("empCategory").value,
      years_of_employment: parseFloat(document.getElementById("yearsEmp").value || 0),
      education: document.getElementById("education").value,
    });
  });

  document.getElementById("financialForm")?.addEventListener("submit", e => {
    e.preventDefault();
    const monthly = parseFloat(document.getElementById("monthlyIncome").value || 0);
    saveCreditProfile({
      monthly_income: monthly,
      annual_income: parseFloat(document.getElementById("annualIncome").value || monthly * 12),
      dependents: parseInt(document.getElementById("dependents").value || 0),
      residence_type: document.getElementById("residenceType").value,
      existing_loans: parseInt(document.getElementById("existingLoans").value || 0),
      existing_emi: parseFloat(document.getElementById("existingEmi").value || 0),
      outstanding_debt: parseFloat(document.getElementById("outstandingDebt").value || 0),
      credit_card_outstanding: parseFloat(document.getElementById("ccOutstanding").value || 0),
      coapplicant: document.getElementById("coapplicant").value === "true",
      coapplicant_income: parseFloat(document.getElementById("coapplicantIncome").value || 0),
    });
  });

  document.getElementById("creditForm")?.addEventListener("submit", e => {
    e.preventDefault();
    saveCreditProfile({
      age: parseInt(document.getElementById("age").value || 25),
      cibil_score: parseInt(document.getElementById("cibilScore").value || 650),
      previous_loans: parseInt(document.getElementById("prevLoans").value || 0),
      missed_payments: parseInt(document.getElementById("missedPayments").value || 0),
      late_payments: parseInt(document.getElementById("latePayments").value || 0),
      average_days_late: parseFloat(document.getElementById("avgDaysLate").value || 0),
    });
  });

  // Auto-compute annual income from monthly
  document.getElementById("monthlyIncome")?.addEventListener("input", function() {
    const annual = parseFloat(this.value || 0) * 12;
    document.getElementById("annualIncome").value = annual || "";
  });
}

function saveCreditProfile(data) {
  laAjax("PUT", "/api/credit-profile", data)
    .then(() => showAlert("profileAlert", "Profile updated successfully.", "success"))
    .catch(err => showAlert("profileAlert", err.message, "danger"));
}
