const API = "/api";

const storage = {
  get access() {
    return localStorage.getItem("access_token");
  },
  get refresh() {
    return localStorage.getItem("refresh_token");
  },
  setTokens(access, refresh) {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  },
  clear() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },
};

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (options.auth && storage.access) {
    headers.Authorization = `Bearer ${storage.access}`;
  }
  if (options.refreshAuth && storage.refresh) {
    headers.Authorization = `Bearer ${storage.refresh}`;
  }

  const res = await fetch(`${API}${path}`, { ...options, headers });
  const json = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, json };
}

function showMessage(el, text, type) {
  if (!el) return;
  el.textContent = text;
  el.className = `message ${type}`;
  el.classList.remove("hidden");
}

function hideMessage(el) {
  if (el) el.classList.add("hidden");
}

function setView(loggedIn) {
  document.getElementById("auth-panel").classList.toggle("hidden", loggedIn);
  document.getElementById("profile-panel").classList.toggle("hidden", !loggedIn);
}

async function checkHealth() {
  const pill = document.getElementById("health-pill");
  const label = document.getElementById("health-label");
  const { ok, json } = await api("/health");

  pill.classList.remove("ok", "bad");
  if (ok && json.data?.database === "connected") {
    pill.classList.add("ok");
    label.textContent = "API · DB connected";
  } else {
    pill.classList.add("bad");
    label.textContent = "API or DB unavailable";
  }
}

async function loadProfile() {
  const { ok, json } = await api("/user/profile", { auth: true });
  if (!ok) {
    storage.clear();
    setView(false);
    return;
  }

  const d = json.data;
  document.getElementById("pf-username").textContent = d.username;
  document.getElementById("pf-email").textContent = d.email;
  document.getElementById("pf-created").textContent = d.created_at || "—";
}

function initTabs() {
  const tabs = document.querySelectorAll(".tab");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const isLogin = tab.dataset.tab === "login";
      loginForm.classList.toggle("hidden", !isLogin);
      registerForm.classList.toggle("hidden", isLogin);
      hideMessage(document.getElementById("auth-message"));
    });
  });
}

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("auth-message");
  hideMessage(msg);

  const body = {
    email: document.getElementById("login-email").value.trim(),
    password: document.getElementById("login-password").value,
  };

  const { ok, json } = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });

  if (!ok) {
    showMessage(msg, json.message || "Login failed", "error");
    return;
  }

  storage.setTokens(json.data.access_token, json.data.refresh_token);
  setView(true);
  await loadProfile();
});

document.getElementById("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("auth-message");
  hideMessage(msg);

  const body = {
    username: document.getElementById("reg-username").value.trim(),
    email: document.getElementById("reg-email").value.trim(),
    password: document.getElementById("reg-password").value,
  };

  const { ok, json } = await api("/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });

  if (!ok) {
    showMessage(msg, json.message || "Registration failed", "error");
    return;
  }

  showMessage(msg, "Account created. Switch to Login.", "success");
  document.querySelector('.tab[data-tab="login"]').click();
});

document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("profile-message");
  hideMessage(msg);

  const body = {};
  const username = document.getElementById("edit-username").value.trim();
  const email = document.getElementById("edit-email").value.trim();
  if (username) body.username = username;
  if (email) body.email = email;

  const { ok, json } = await api("/user/profile", {
    method: "PUT",
    auth: true,
    body: JSON.stringify(body),
  });

  if (!ok) {
    showMessage(msg, json.message || "Update failed", "error");
    return;
  }

  showMessage(msg, json.message, "success");
  document.getElementById("edit-username").value = "";
  document.getElementById("edit-email").value = "";
  await loadProfile();
});

document.getElementById("logout-btn").addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST", auth: true });
  storage.clear();
  setView(false);
  hideMessage(document.getElementById("profile-message"));
});

document.getElementById("refresh-btn").addEventListener("click", async () => {
  const msg = document.getElementById("profile-message");
  const { ok, json } = await api("/auth/refresh", {
    method: "POST",
    refreshAuth: true,
  });

  if (!ok) {
    showMessage(msg, json.message || "Refresh failed", "error");
    return;
  }

  localStorage.setItem("access_token", json.data.access_token);
  showMessage(msg, "Access token refreshed", "success");
});

if (storage.access) {
  setView(true);
  loadProfile();
} else {
  setView(false);
}

initTabs();
checkHealth();
