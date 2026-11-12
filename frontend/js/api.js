const Api = {
  csrf: null,

  async request(method, path, body) {
    const headers = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (method !== "GET" && this.csrf) headers["X-CSRF-Token"] = this.csrf;

    let res;
    try {
      res = await fetch(path, {
        method,
        headers,
        credentials: "same-origin",
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch {
      return { ok: false, status: 0, data: null,
               message: "Cannot reach the server. Check that it is running." };
    }

    let data = null;
    if (res.status !== 204) {
      try { data = await res.json(); } catch { /* no JSON body */ }
    }
    return {
      ok: res.ok,
      status: res.status,
      data,
      message: res.ok ? null : Api.errorMessage(data),
    };
  },

  errorMessage(data) {
    const detail = data && data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length) {
      return detail
        .map((e) => String(e.msg || "").replace(/^Value error,\s*/, ""))
        .join(" ");
    }
    return "Something went wrong. Please try again.";
  },

  get(path) { return this.request("GET", path); },
  post(path, body) { return this.request("POST", path, body); },
  put(path, body) { return this.request("PUT", path, body); },
  del(path) { return this.request("DELETE", path); },
};

// Returns the logged-in user, or null. Also stores the CSRF token for later requests.
async function loadSession() {
  const res = await Api.get("/auth/me");
  if (res.ok) {
    Api.csrf = res.data.csrf_token;
    return res.data.user;
  }
  return null;
}