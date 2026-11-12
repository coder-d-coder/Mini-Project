function setStatus(el, type, text) {
  if (!text) { el.hidden = true; el.textContent = ""; return; }
  el.hidden = false;
  el.className = "status " + type;
  el.textContent = text;
}

function setFieldError(inputId, message) {
  const input = document.getElementById(inputId);
  const err = document.getElementById(inputId + "-error");
  input.setAttribute("aria-invalid", message ? "true" : "false");
  err.textContent = message || "";
}

function clearFieldErrors(form) {
  form.querySelectorAll("input").forEach((i) => setFieldError(i.id, ""));
}

function setupPasswordToggles() {
  document.querySelectorAll(".toggle-password").forEach((btn) => {
    const input = document.getElementById(btn.dataset.target);
    btn.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
      btn.setAttribute("aria-pressed", String(show));
      btn.setAttribute("aria-label", (show ? "Hide " : "Show ") + btn.dataset.label);
    });
  });
}

function setLoading(button, loading, idleText, busyText) {
  button.disabled = loading;
  button.textContent = loading ? busyText : idleText;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// ---------- Login page ----------
function initLogin() {
  const form = document.getElementById("login-form");
  const status = document.getElementById("form-status");
  const button = form.querySelector("button[type=submit]");

  if (new URLSearchParams(location.search).get("registered") === "1") {
    setStatus(status, "success", "Account created. Please sign in.");
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFieldErrors(form);
    setStatus(status, "", "");

    const email = form.email.value.trim();
    const password = form.password.value;
    let valid = true;
    if (!EMAIL_PATTERN.test(email)) { setFieldError("email", "Enter a valid email address."); valid = false; }
    if (!password) { setFieldError("password", "Enter your password."); valid = false; }
    if (!valid) return;

    setLoading(button, true, "Sign in", "Signing in...");
    const res = await Api.post("/auth/login", { email, password });
    if (res.ok) {
      Api.csrf = res.data.csrf_token;
      location.href = "dashboard.html";
      return;
    }
    setLoading(button, false, "Sign in", "Signing in...");
    setStatus(status, "error", res.message);
  });
}

// ---------- Register page ----------
function initRegister() {
  const form = document.getElementById("register-form");
  const status = document.getElementById("form-status");
  const button = form.querySelector("button[type=submit]");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFieldErrors(form);
    setStatus(status, "", "");

    const name = form.name.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;
    const confirm = form.confirm_password.value;
    let valid = true;

    if (!name) { setFieldError("name", "Enter your full name."); valid = false; }
    if (!EMAIL_PATTERN.test(email)) { setFieldError("email", "Enter a valid email address."); valid = false; }
    if (password.length < 10) {
      setFieldError("password", "Use at least 10 characters."); valid = false;
    } else if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      setFieldError("password", "Include at least one letter and one number."); valid = false;
    }
    if (confirm !== password) { setFieldError("confirm_password", "Passwords do not match."); valid = false; }
    if (!valid) return;

    setLoading(button, true, "Create account", "Creating account...");
    const res = await Api.post("/auth/register", {
      name, email, password, confirm_password: confirm,
    });

    if (res.ok) {
      setStatus(status, "success", "Account created. Redirecting to sign in...");
      setTimeout(() => { location.href = "login.html?registered=1"; }, 1200);
      return;
    }
    setLoading(button, false, "Create account", "Creating account...");
    if (res.status === 409) setFieldError("email", res.message);
    setStatus(status, "error", res.message);
  });
}

// ---------- Startup ----------
setupPasswordToggles();
loadSession().then((user) => {
  if (user) location.replace("dashboard.html"); // already signed in
});
if (document.getElementById("login-form")) initLogin();
if (document.getElementById("register-form")) initRegister();