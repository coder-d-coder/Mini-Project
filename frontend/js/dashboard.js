const $ = (id) => document.getElementById(id);
const state = { profile: null, saved: [], totalSkills: 0 };

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
const tag = (text, cls) => el("span", "tag " + cls, text);

function setStatus(node, type, text) {
  if (!text) { node.hidden = true; node.textContent = ""; return; }
  node.hidden = false;
  node.className = "status " + type;
  node.textContent = text;
}

function emptyState(container, text) {
  container.textContent = "";
  container.appendChild(el("p", "empty", text));
}

// Redirects to login if the session is gone; returns true when the response is usable.
function ok(res) {
  if (res.status === 401) { location.replace("login.html"); return false; }
  return res.ok;
}

function salary(min, max) {
  if (min == null || max == null) return "";
  const lakh = (n) => (n / 100000).toFixed(1).replace(/\.0$/, "");
  return ` · ₹${lakh(min)}–${lakh(max)} lakh per year`;
}

// ---------- rendering ----------
function renderHeader() {
  const p = state.profile;
  $("menu-name").textContent = p.name;
  $("menu-email").textContent = p.email;
  $("welcome-title").textContent = "Welcome back, " + p.name.split(" ")[0];

  let text;
  if (p.skills.length === 0) {
    text = "Start by choosing your skills in the career search panel. Your recommendations will appear right after.";
  } else {
    text = `You have ${p.skills.length} skill${p.skills.length === 1 ? "" : "s"} selected`;
    text += p.target_role ? ` and are aiming for ${p.target_role}.` : ". Pick a target role to prioritise matching jobs.";
  }
  $("welcome-text").textContent = text;
  $("stat-skills").textContent = p.skills.length;
  $("stat-skills-note").textContent = `of ${state.totalSkills} available`;
}

function renderSearchForm(roles, allSkills) {
  const select = $("role");
  select.textContent = "";
  const none = el("option", "", "No target role");
  none.value = "";
  select.appendChild(none);
  for (const r of roles) {
    const o = el("option", "", r);
    o.value = r;
    select.appendChild(o);
  }
  select.value = state.profile.target_role || "";

  const have = new Set(state.profile.skills.map((s) => s.name));
  const grid = $("skill-grid");
  grid.textContent = "";
  for (const s of allSkills) {
    const label = el("label");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.value = s.name;
    box.checked = have.has(s.name);
    label.append(box, " " + s.name);
    grid.appendChild(label);
  }
}

function renderJobs(items) {
  const box = $("jobs-list");
  if (state.profile.skills.length === 0) {
    return emptyState(box, "No recommendations yet. Select your skills and press Update recommendations.");
  }
  if (items.length === 0) {
    return emptyState(box, "No sample jobs match your skills yet. Try adding more skills.");
  }
  box.textContent = "";
  for (const item of items) {
    const card = el("article", "job-card");
    const head = el("div", "job-head");
    head.append(el("h3", "", item.job.title), el("span", "score", item.score + "% fit"));

    const place = item.job.location || "Location not listed";
    card.append(head, el("p", "meta", `${item.job.company} · ${place}${salary(item.job.salary_min, item.job.salary_max)}`));

    if (item.role_match) card.appendChild(tag("Matches your target role", "role-tag"));

    const have = el("div", "tag-row", "You have: ");
    item.matched_skills.forEach((s) => have.appendChild(tag(s, "have")));
    card.appendChild(have);

    if (item.missing_skills.length) {
      const lack = el("div", "tag-row", "Missing: ");
      item.missing_skills.forEach((s) => lack.appendChild(tag(s, "lack")));
      card.appendChild(lack);
    }
    const save = el("button", "btn btn-secondary save-btn", "Save job");
    save.type = "button";
    save.dataset.jobId = item.job.id;
    save.addEventListener("click", () => toggleSave(item.job, save));
    card.appendChild(save);
    box.appendChild(card);
  }
}

function renderGap(data) {
  const list = $("gap-list");
  const resBox = $("resource-list");
  list.textContent = "";

  const scope = data.role ? `${data.role} jobs` : "your top matches";
  $("gap-note").textContent = data.gaps.length
    ? `Skills missing most often across ${data.based_on_jobs} of ${scope}.`
    : "Your skill gaps will show here once you have recommendations.";

  if (data.gaps.length === 0) {
    emptyState(resBox, "Learning links appear here when you have skill gaps.");
    return;
  }

  resBox.textContent = "";
  for (const g of data.gaps) {
    const li = el("li");
    li.append(el("strong", "", g.skill), el("span", "hint", `needed by ${g.needed_by} job${g.needed_by === 1 ? "" : "s"}`));
    list.appendChild(li);

    const group = el("div", "resource-group");
    group.appendChild(el("h3", "", g.skill));
    if (g.resources.length === 0) {
      group.appendChild(el("p", "hint", "No curated resource yet. Search the official documentation."));
    } else {
      const ul = el("ul", "resource-list");
      for (const r of g.resources) {
        const item = el("li");
        if (r.url.startsWith("https://")) {
          const a = el("a", "", r.title);
          a.href = r.url;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          item.appendChild(a);
        } else {
          item.appendChild(el("span", "", r.title));
        }
        item.appendChild(el("span", "kind", " · " + r.kind));
        ul.appendChild(item);
      }
      group.appendChild(ul);
    }
    resBox.appendChild(group);
  }
}

function renderStats(items) {
  const best = items.length ? Math.max(...items.map((i) => i.score)) : null;
  $("stat-match").textContent = best === null ? "\u2014" : best + "%";
  $("stat-match-note").textContent = best === null
    ? "Select skills to see your top fit."
    : "Highest skill fit among the sample jobs.";
}

function isSaved(jobId) {
  return state.saved.some((s) => s.job.id === jobId);
}

function syncSaveButtons() {
  document.querySelectorAll("#jobs-list .save-btn").forEach((btn) => {
    const saved = isSaved(Number(btn.dataset.jobId));
    btn.textContent = saved ? "Saved \u2713" : "Save job";
    btn.setAttribute("aria-pressed", String(saved));
  });
}

function renderSaved() {
  const box = $("saved-list");
   if (state.saved.length === 0) {
     return emptyState(box, "No saved jobs yet. Use Save job on a recommendation and it will appear here.");
   }
   box.textContent = "";
   for (const s of state.saved) {
     const row = el("div", "saved-item");
     const info = el("div");
     info.append(el("h3", "", s.job.title), el("p", "", `${s.job.company} \u00b7 ${s.job.location || "Location not listed"}`));
     const remove = el("button", "btn btn-secondary save-btn", "Remove");
     remove.type = "button";
     remove.setAttribute("aria-label", "Remove " + s.job.title + " from saved jobs");
     remove.addEventListener("click", () => toggleSave(s.job, remove));
     row.append(info, remove);
     box.appendChild(row);
   }
}

async function refreshSaved() {
  const res = await Api.get("/me/saved-jobs");
  if (ok(res)) { state.saved = res.data; renderSaved(); syncSaveButtons(); }
  return res;
}

async function toggleSave(job, button) {
  const status = $("saved-status");
  setStatus(status, "", "");
  button.disabled = true;
  const path = `/me/saved-jobs/${job.id}`;
  const res = isSaved(job.id) ? await Api.del(path) : await Api.post(path);
  button.disabled = false;
  if (res.status === 401) return location.replace("login.html");
  if (!res.ok) return setStatus(status, "error", res.message);
  await refreshSaved();
}

// ---------- data loading ----------
async function loadInsights() {
  const [recs, gap] = await Promise.all([Api.get("/me/recommendations"), Api.get("/me/skill-gap")]);
  if (ok(recs)) { renderJobs(recs.data); renderStats(recs.data); }
  else emptyState($("jobs-list"), "Could not load recommendations. " + (recs.message || ""));
  if (ok(gap)) renderGap(gap.data);
  else emptyState($("resource-list"), "Could not load skill gaps. " + (gap.message || ""));
  await refreshSaved();
}

function profilePayload(overrides) {
  const p = state.profile;
  return {
    name: p.name,
    location: p.location,
    experience_years: p.experience_years ?? 0,
    target_role: p.target_role,
    skills: p.skills.map((s) => s.name),
    ...overrides,
  };
}

async function saveProfile(overrides) {
  const res = await Api.put("/me/profile", profilePayload(overrides));
  if (ok(res)) state.profile = res.data;
  return res;
}

// ---------- events ----------
function setupMenu() {
  const btn = $("menu-btn");
  const menu = $("menu");
  const close = () => { menu.hidden = true; btn.setAttribute("aria-expanded", "false"); };
  btn.addEventListener("click", () => {
    const open = menu.hidden;
    menu.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", (e) => {
    if (!menu.hidden && !menu.contains(e.target) && !btn.contains(e.target)) close();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !menu.hidden) { close(); btn.focus(); }
  });

  $("logout").addEventListener("click", async () => {
    await Api.post("/auth/logout");
    location.href = "login.html";
  });

  $("edit-profile").addEventListener("click", () => {
    close();
    const p = state.profile;
    $("p-name").value = p.name;
    $("p-location").value = p.location || "";
    $("p-exp").value = p.experience_years ?? 0;
    setStatus($("profile-status"), "", "");
    $("profile-dialog").showModal();
  });
}

function setupForms() {
  $("p-cancel").addEventListener("click", () => $("profile-dialog").close());

  $("profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = $("p-name").value.trim();
    if (!name) return setStatus($("profile-status"), "error", "Enter your full name.");
    const res = await saveProfile({
      name,
      location: $("p-location").value.trim() || null,
      experience_years: Number($("p-exp").value) || 0,
    });
    if (!res.ok) return setStatus($("profile-status"), "error", res.message);
    $("profile-dialog").close();
    renderHeader();
    loadInsights();
  });

  $("search-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = $("search-status");
    setStatus(status, "", "");
    const skills = [...document.querySelectorAll("#skill-grid input:checked")].map((b) => b.value);
    const button = e.target.querySelector("button[type=submit]");
    button.disabled = true;
    button.textContent = "Updating...";
    const res = await saveProfile({ skills, target_role: $("role").value || null });
    button.disabled = false;
    button.textContent = "Update recommendations";
    if (!res.ok) return setStatus(status, "error", res.message);
    setStatus(status, "success", "Saved. Recommendations updated.");
    renderHeader();
    loadInsights();
  });
}

// ---------- startup ----------
(async function () {
  const user = await loadSession();
  if (!user) { location.replace("login.html"); return; }

  const [profile, roles, skills] = await Promise.all([
    Api.get("/me/profile"), Api.get("/me/roles"), Api.get("/skills"),
  ]);
  if (!ok(profile) || !roles.ok || !skills.ok) {
    $("welcome-title").textContent = "Could not load your dashboard";
    $("welcome-text").textContent = "Check that the server is running, then refresh the page.";
    return;
  }

  state.profile = profile.data;
  state.totalSkills = skills.data.length;
  renderHeader();
  renderSearchForm(roles.data, skills.data);
  setupMenu();
  setupForms();
  loadInsights();
})();