const API_BASE = "http://127.0.0.1:5000";

const $ = (id) => document.getElementById(id);

function setMessage(id, text, type = "") {
  const el = $(id);
  if (!el) return;
  el.textContent = text;
  el.className = `message ${type}`.trim();
}

function setButtonLoading(button, loading, loadingText, normalText) {
  if (!button) return;
  button.disabled = loading;
  const span = button.querySelector("span");
  if (span) span.textContent = loading ? loadingText : normalText;
}

function showLogin() {
  $("loginBox")?.classList.remove("hidden");
  $("registerBox")?.classList.add("hidden");
  setMessage("registerMessage", "");
  setTimeout(() => $("loginEmail")?.focus(), 50);
}

function showRegister() {
  $("loginBox")?.classList.add("hidden");
  $("registerBox")?.classList.remove("hidden");
  setMessage("loginMessage", "");
  setTimeout(() => $("registerName")?.focus(), 50);
}

document.querySelectorAll(".password-toggle").forEach(btn => {
  btn.addEventListener("click", () => {
    const input = $(btn.dataset.target);
    if (!input) return;
    const visible = input.type === "text";
    input.type = visible ? "password" : "text";
    btn.textContent = visible ? "Show" : "Hide";
    btn.setAttribute("aria-label", visible ? "Show password" : "Hide password");
  });
});

const registerForm = $("registerForm");
registerForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = $("registerName").value.trim();
  const email = $("registerEmail").value.trim().toLowerCase();
  const password = $("registerPassword").value;

  if (name.length < 2) return setMessage("registerMessage", "Please enter your full name.", "error");
  if (!email || !email.includes("@")) return setMessage("registerMessage", "Please enter a valid email.", "error");
  if (password.length < 4) return setMessage("registerMessage", "Password must be at least 4 characters.", "error");

  const button = $("registerBtn");
  setMessage("registerMessage", "Creating your account...", "info");
  setButtonLoading(button, true, "Creating...", "Create Account");

  try {
    const response = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({name, email, password})
    });

    const data = await response.json().catch(() => ({}));

    if (response.ok && data.success) {
      setMessage("registerMessage", "Account created! Opening login...", "success");
      registerForm.reset();

      setTimeout(() => {
        showLogin();
        $("loginEmail").value = email;
      }, 900);
    } else {
      setMessage("registerMessage", data.message || "Registration failed.", "error");
    }
  } catch (error) {
    console.error(error);
    setMessage("registerMessage", "Backend is not reachable. Start app.py and try again.", "error");
  } finally {
    setButtonLoading(button, false, "Creating...", "Create Account");
  }
});

const loginForm = $("loginForm");
loginForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = $("loginEmail").value.trim().toLowerCase();
  const password = $("loginPassword").value;

  if (!email || !password) return setMessage("loginMessage", "Email and password are required.", "error");

  const button = $("loginBtn");
  setMessage("loginMessage", "Signing you in...", "info");
  setButtonLoading(button, true, "Logging in...", "Login");

  try {
    const response = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({email, password})
    });

    const data = await response.json().catch(() => ({}));

    if (response.ok && data.success && data.user) {
      const user = {
        ...data.user,
        id: data.user.id ?? data.user.user_id,
        user_id: data.user.user_id ?? data.user.id
      };

      localStorage.setItem("user", JSON.stringify(user));
      localStorage.removeItem("cart");
      setMessage("loginMessage", "Login successful! Opening dashboard...", "success");

      setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 450);
    } else {
      setMessage("loginMessage", data.message || "Invalid email or password.", "error");
    }
  } catch (error) {
    console.error(error);
    setMessage("loginMessage", "Backend is not reachable. Start app.py and try again.", "error");
  } finally {
    setButtonLoading(button, false, "Logging in...", "Login");
  }
});
