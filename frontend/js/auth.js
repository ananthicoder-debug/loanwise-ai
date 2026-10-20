/* ===================================================================
   LoanWise AI — auth.js
   Login and Register page logic
=================================================================== */

function initLoginPage() {
  document.getElementById("togglePwd")?.addEventListener("click", function() {
    const pwd = document.getElementById("loginPassword");
    pwd.type = pwd.type === "password" ? "text" : "password";
  });

  document.getElementById("loginForm")?.addEventListener("submit", function(e) {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const btn = document.getElementById("loginBtn");

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Signing in...';

    laAjax("POST", "/api/auth/login", { email, password })
      .then(response => {
        setSession(response.access_token, response.role, response.full_name);
        window.location.href = response.role === "admin" ? "admin-dashboard.html" : "dashboard.html";
      })
      .catch(err => {
        showAlert("loginAlert", err.message, "danger");
        btn.disabled = false;
        btn.textContent = "Sign In";
      });
  });
}

function initRegisterPage() {
  document.getElementById("toggleRegPwd")?.addEventListener("click", function() {
    const pwd = document.getElementById("regPassword");
    pwd.type = pwd.type === "password" ? "text" : "password";
  });

  document.getElementById("registerForm")?.addEventListener("submit", function(e) {
    e.preventDefault();
    const full_name = document.getElementById("regName").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const phone = document.getElementById("regPhone").value.trim();
    const password = document.getElementById("regPassword").value;
    const btn = document.getElementById("registerBtn");

    if (!/^\d{10}$/.test(phone)) {
      showAlert("registerAlert", "Please enter a valid 10-digit mobile number.", "warning");
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating account...';

    laAjax("POST", "/api/auth/register", { full_name, email, phone, password })
      .then(response => {
        setSession(response.access_token, response.role, response.full_name);
        window.location.href = "dashboard.html";
      })
      .catch(err => {
        showAlert("registerAlert", err.message, "danger");
        btn.disabled = false;
        btn.textContent = "Create Account";
      });
  });
}
