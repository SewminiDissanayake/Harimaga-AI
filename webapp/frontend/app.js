const convo = document.getElementById("conversation");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const choiceArea = document.getElementById("choiceArea");
const newBtn = document.getElementById("newBtn");
const backendStatus = document.getElementById("backendStatus");
const statusDot = document.getElementById("statusDot");
const promptButtons = document.querySelectorAll("[data-prompt]");
const attachBtn = document.getElementById("attachBtn");
const evidenceInput = document.getElementById("evidenceInput");
const evidenceTray = document.getElementById("evidenceTray");
const evidenceList = document.getElementById("evidenceList");
const evidenceCount = document.getElementById("evidenceCount");
const evidenceToolbarBtn = document.getElementById("evidenceToolbarBtn");
const evidenceUploadStatus = document.getElementById("evidenceUploadStatus");
const sendEvidenceBtn = document.getElementById("sendEvidenceBtn");
const pendingEvidenceTray = document.getElementById("pendingEvidenceTray");
const pendingEvidenceList = document.getElementById("pendingEvidenceList");
const pendingEvidenceCount = document.getElementById("pendingEvidenceCount");
const draftModal = document.getElementById("draftModal");
const draftSubject = document.getElementById("draftSubject");
const draftBody = document.getElementById("draftBody");
const closeDraftBtn = document.getElementById("closeDraftBtn");
const doneDraftBtn = document.getElementById("doneDraftBtn");
const copyDraftBtn = document.getElementById("copyDraftBtn");

let originalText = "";
let answers = {};
let pendingField = null;
let evidenceItems = [];
let pendingEvidence = [];
let lastRoutingData = null;

function newAnonymousRequestId() {
  if (window.crypto?.randomUUID) {
    return `hm_${window.crypto.randomUUID().replaceAll("-", "")}`;
  }
  return `hm_${Date.now()}_${Math.random().toString(36).slice(2, 14)}`;
}

let requestId = sessionStorage.getItem("harimaga_request_id") || newAnonymousRequestId();
sessionStorage.setItem("harimaga_request_id", requestId);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;");
}

function humanize(value) {
  return String(value ?? "")
    .replaceAll("_"," ")
    .replace(/\b\w/g, c => c.toUpperCase());
}

function setStep(n) {
  document.querySelectorAll(".step").forEach((el, i) => {
    el.classList.toggle("active", i + 1 === n);
    el.classList.toggle("done", i + 1 < n);
  });
}

function addMessage(role, innerHtml) {
  const wrap = document.createElement("div");
  wrap.className = `message ${role}`;
  if (role === "assistant") {
    wrap.innerHTML = `
      <div class="msg-avatar"><img src="/frontend/assets/harimaga-logo.svg" alt=""></div>
      <div class="bubble">${innerHtml}</div>`;
  } else {
    wrap.innerHTML = `<div class="bubble">${innerHtml}</div>`;
  }
  convo.appendChild(wrap);
  convo.scrollTop = convo.scrollHeight;
  return wrap;
}

function clearChoices() {
  choiceArea.innerHTML = "";
  choiceArea.classList.add("hidden");
}

function optionValueLabel(option) {
  if (option && typeof option === "object") {
    return {
      value: Object.prototype.hasOwnProperty.call(option, "value") ? option.value : option.label,
      label: option.label ?? option.value
    };
  }
  return {value: option, label: option};
}

function renderClarification(routing) {
  pendingField = routing.needed_field;
  setStep(2);
  addMessage(
    "assistant",
    `<div class="msg-name">HariMaga Guide</div>
     <p>${escapeHtml(routing.question || "I need one more detail.")}</p>`
  );

  clearChoices();

  if (Array.isArray(routing.options) && routing.options.length) {
    choiceArea.classList.remove("hidden");
    routing.options.forEach(option => {
      const {value, label} = optionValueLabel(option);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = label;
      btn.addEventListener("click", () => submitClarification(value, label));
      choiceArea.appendChild(btn);
    });
  }

  input.placeholder = routing.allow_skip ? "Type your answer, or 'skip'..." : "Type your answer...";
  input.focus();
}

function routeTitle(data) {
  const r = data.routing || {};
  const cls = data.classification || {};
  return (
    r.subtype_label ||
    r.label ||
    r.document?.label ||
    r.jurisdiction?.authority_name ||
    r.authority?.name ||
    r.authority_name ||
    humanize(r.issue_key || cls.label)
  );
}

function routeAuthority(r) {
  return (
    r.technical_authority ||
    r.jurisdiction?.authority_name ||
    r.document?.authority ||
    r.authority?.name ||
    (typeof r.authority === "string" ? r.authority : "") ||
    r.authority_name ||
    ""
  );
}

function channelLines(record) {
  const lines = [];
  if (!record || typeof record !== "object") return lines;

  const channels = record.channels;
  if (Array.isArray(channels)) {
    channels.forEach(ch => {
      const label = ch.label || humanize(ch.type) || "Official channel";
      const val = ch.value || ch.phone || ch.email || ch.url;
      if (val) lines.push(`${label}: ${val}`);
    });
  }

  const direct = [
    ["Hotline", record.hotline],
    ["Phone", record.phone],
    ["Telephone", record.telephone],
    ["Mobile", record.mobile],
    ["WhatsApp", record.whatsapp],
    ["Email", record.email],
    ["Website", record.website],
    ["Official link", record.url],
    ["Online complaint form", record.online_complaint_form],
    ["Consumer Complaint Unit", record.consumer_complaint_unit],
  ];

  direct.forEach(([label,val]) => {
    if (val && typeof val !== "object") lines.push(`${label}: ${val}`);
  });

  return lines;
}

function unique(arr) {
  return [...new Set(arr.filter(Boolean))];
}

function collectVerifiedChannels(r) {
  let lines = [];

  [
    r.verified_provider_route,
    r.verified_authority_route,
    r.verified_ntc_fallback
  ].forEach(x => lines.push(...channelLines(x)));

  if (Array.isArray(r.verified_local_authority_routes)) {
    r.verified_local_authority_routes.forEach(row => {
      const name = row.authority?.name || "Local authority";
      if (row.verified_issue_channel) {
        channelLines(row.verified_issue_channel).forEach(x => lines.push(`${name} — ${x}`));
      } else if (row.directory_fallback) {
        const f = row.directory_fallback;
        const phones = [...(f.phones || []), ...(f.mobiles || [])];
        phones.forEach(p => lines.push(`${name} directory fallback — Phone: ${p}`));
        (f.emails || []).forEach(e => lines.push(`${name} directory fallback — Email: ${e}`));
      }
    });
  }

  if (Array.isArray(r.contacts)) {
    r.contacts.forEach(c => {
      const prefix = c.label || "Official contact";
      if (c.phone) lines.push(`${prefix} — Phone: ${c.phone}`);
      if (c.email) lines.push(`${prefix} — Email: ${c.email}`);
      if (c.url) lines.push(`${prefix} — Link: ${c.url}`);
    });
  }

  if (r.authority && typeof r.authority === "object") {
    const a = r.authority;
    if (a.hotline) lines.push(`Hotline: ${a.hotline}`);
    if (a.consumer_complaint_unit) lines.push(`Consumer Complaint Unit: ${a.consumer_complaint_unit}`);
    if (a.online_complaint_form) lines.push(`Online complaint form: ${a.online_complaint_form}`);
  }

  if (r.district_office) {
    const d = r.district_office;
    if (d.office) lines.push(`${d.office}${d.telephone ? " — " + d.telephone : ""}`);
  }

  if (r.document?.contacts) {
    r.document.contacts.forEach(c => {
      if (c.value) lines.push(`${c.label}: ${c.value}`);
    });
  }

  if (Array.isArray(r.police_station_matches)) {
    r.police_station_matches.slice(0,5).forEach(p => {
      const parts = [];
      if (p.general) parts.push(`General: ${p.general}`);
      if (p.mobile) parts.push(`Mobile: ${p.mobile}`);
      if (p.email) parts.push(`Email: ${p.email}`);
      lines.push(`${p.station || "Police station"}${parts.length ? " — " + parts.join(" · ") : ""}`);
    });
  }

  if (Array.isArray(r.dmc_contacts)) {
    r.dmc_contacts.forEach(c => {
      if (c.phone) lines.push(`${c.label}: ${c.phone}`);
      if (c.email) lines.push(`${c.label}: ${c.email}`);
    });
  }

  if (Array.isArray(r.technical_contacts)) {
    r.technical_contacts.forEach(c => {
      if (c.phone) lines.push(`${c.label}: ${c.phone}`);
      if (c.email) lines.push(`${c.label}: ${c.email}`);
    });
  }

  return unique(lines).slice(0,16);
}

function collectRequiredInfo(r) {
  let items = [];
  if (Array.isArray(r.required_information)) items.push(...r.required_information);
  if (Array.isArray(r.document?.required_information)) items.push(...r.document.required_information);
  return unique(items).slice(0,14);
}

function collectSteps(r) {
  if (Array.isArray(r.document?.steps)) return r.document.steps;
  if (Array.isArray(r.steps)) return r.steps;
  return [];
}

function resultSection(title, items, extraClass="") {
  if (!items.length) return "";
  return `
    <div class="result-section ${extraClass}">
      <h5>${escapeHtml(title)}</h5>
      <ul>${items.map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
    </div>`;
}


function fileSizeLabel(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function sanitizeImageFile(file) {
  const name = String(file.name || "").toLowerCase();

  if (name.endsWith(".heic") || name.endsWith(".heif")) {
    throw new Error("HEIC/HEIF photo detected. Please export or save it as JPG, then attach it again.");
  }

  if (!file.type.startsWith("image/")) {
    return {file, privacyProcessed:false};
  }

  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch (err) {
    throw new Error("This photo format could not be opened by the browser. Please use JPG, PNG, WEBP, or PDF.");
  }
  const maxSide = 1800;
  let width = bitmap.width;
  let height = bitmap.height;
  const scale = Math.min(1, maxSide / Math.max(width, height));
  width = Math.max(1, Math.round(width * scale));
  height = Math.max(1, Math.round(height * scale));

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(bitmap, 0, 0, width, height);

  let outputType = file.type;
  if (!["image/jpeg","image/png","image/webp"].includes(outputType)) {
    outputType = "image/jpeg";
  }

  const blob = await new Promise((resolve, reject) => {
    canvas.toBlob(
      b => b ? resolve(b) : reject(new Error("Could not prepare image evidence.")),
      outputType,
      outputType === "image/jpeg" || outputType === "image/webp" ? 0.9 : undefined
    );
  });

  const safeFile = new File([blob], file.name, {
    type: outputType,
    lastModified: Date.now()
  });

  return {file:safeFile, privacyProcessed:true};
}

async function uploadEvidenceFile(file) {
  if (evidenceItems.length >= 6) {
    throw new Error("Maximum 6 evidence files per request.");
  }

  if (file.size > 10 * 1024 * 1024) {
    throw new Error(`${file.name} is larger than 10 MB.`);
  }

  const {file:prepared, privacyProcessed} = await sanitizeImageFile(file);

  const formData = new FormData();
  formData.append("file", prepared);
  formData.append("privacy_processed", privacyProcessed ? "true" : "false");
  formData.append("request_id", requestId);

  const res = await fetch("/api/evidence", {
    method: "POST",
    body: formData
  });
  const data = await res.json();

  if (!res.ok || !data.ok) {
    throw new Error(data.error || "Evidence upload failed.");
  }

  evidenceItems.push(data.evidence);
  renderEvidenceTray();
  return data.evidence;
}

async function removeEvidence(id) {
  try {
    await fetch(`/api/evidence/${encodeURIComponent(id)}`, {
      method:"DELETE",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({request_id:requestId})
    });
  } catch {}
  evidenceItems = evidenceItems.filter(x => x.id !== id);
  renderEvidenceTray();
}


function clearPendingEvidence() {
  pendingEvidence.forEach(item => {
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
  });
  pendingEvidence = [];
  renderPendingEvidence();
}

function removePendingEvidence(index) {
  const item = pendingEvidence[index];
  if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl);
  pendingEvidence.splice(index, 1);
  renderPendingEvidence();
}

function renderPendingEvidence() {
  pendingEvidenceList.innerHTML = "";
  pendingEvidenceCount.textContent = `${pendingEvidence.length} selected`;

  if (!pendingEvidence.length) {
    pendingEvidenceTray.classList.add("hidden");
    sendEvidenceBtn.classList.add("hidden");
    if (!evidenceItems.length) {
      evidenceUploadStatus.textContent = "No evidence attached";
      evidenceUploadStatus.className = "";
    }
    return;
  }

  pendingEvidenceTray.classList.remove("hidden");
  sendEvidenceBtn.classList.remove("hidden");
  evidenceUploadStatus.textContent = `${pendingEvidence.length} selected — not attached yet`;
  evidenceUploadStatus.className = "busy";

  pendingEvidence.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "evidence-item";

    const isImage = String(item.file.type || "").startsWith("image/");
    const preview = isImage
      ? `<img src="${escapeHtml(item.previewUrl)}" alt="Selected evidence preview">`
      : `<span class="pdf-preview">PDF</span>`;

    card.innerHTML = `
      <button class="remove-evidence" type="button" aria-label="Remove selected file">×</button>
      <div class="evidence-preview">${preview}</div>
      <div class="evidence-meta">
        <b>${escapeHtml(item.file.name)}</b>
        <span>${escapeHtml(fileSizeLabel(item.file.size))}</span>
        <span class="pending-state">Selected · waiting to attach</span>
      </div>`;

    card.querySelector(".remove-evidence").addEventListener(
      "click",
      () => removePendingEvidence(index)
    );

    pendingEvidenceList.appendChild(card);
  });
}

async function restoreEvidenceForRequest() {
  try {
    const res = await fetch(`/api/evidence/request/${encodeURIComponent(requestId)}`);
    const data = await res.json();

    if (!res.ok || !data.ok) return;

    evidenceItems = Array.isArray(data.evidence) ? data.evidence : [];
    renderEvidenceTray();
  } catch {}
}

function renderEvidenceTray() {
  evidenceList.innerHTML = "";
  evidenceCount.textContent = `${evidenceItems.length} / 6`;

  if (!evidenceItems.length) {
    evidenceTray.classList.add("hidden");
    evidenceUploadStatus.textContent = "No evidence attached";
    evidenceUploadStatus.className = "";
    return;
  }

  evidenceTray.classList.remove("hidden");

  evidenceUploadStatus.textContent = `${evidenceItems.length} evidence file${evidenceItems.length === 1 ? "" : "s"} attached ✓`;
  evidenceUploadStatus.className = "ok";

  evidenceItems.forEach(item => {
    const card = document.createElement("div");
    card.className = "evidence-item";

    const isImage = String(item.mime_type || "").startsWith("image/");
    const preview = isImage
      ? `<img src="${escapeHtml(item.preview_url)}" alt="Evidence preview">`
      : `<span class="pdf-preview">PDF</span>`;

    card.innerHTML = `
      <button class="remove-evidence" type="button" aria-label="Remove ${escapeHtml(item.filename)}">×</button>
      <div class="evidence-preview">${preview}</div>
      <div class="evidence-meta">
        <b title="${escapeHtml(item.filename)}">${escapeHtml(item.filename)}</b>
        <span>${escapeHtml(fileSizeLabel(item.size_bytes || 0))}${item.privacy_processed ? " · metadata-cleaned image" : ""}</span>
        <span class="upload-state">Attached ✓ · auto-deletes within 24h</span>
      </div>`;

    card.querySelector(".remove-evidence").addEventListener("click", () => removeEvidence(item.id));
    evidenceList.appendChild(card);
  });
}

function findOfficialActions(value, actions = [], seen = new Set()) {
  if (value === null || value === undefined) return actions;

  if (Array.isArray(value)) {
    value.forEach(v => findOfficialActions(v, actions, seen));
    return actions;
  }

  if (typeof value !== "object") return actions;

  const label = value.label || value.name || value.office || value.authority_name || "Official channel";

  for (const [key, raw] of Object.entries(value)) {
    if (typeof raw !== "string") continue;
    const val = raw.trim();
    if (!val) continue;

    let action = null;

    if (/^https?:\/\//i.test(val)) {
      action = {type:"url", label:key.toLowerCase().includes("complaint") ? "Open complaint portal" : "Open official website", value:val};
    } else if (key.toLowerCase().includes("email") && val.includes("@")) {
      action = {type:"email", label:"Email authority", value:val};
    } else if (
      ["phone","telephone","mobile","hotline","whatsapp","value"].includes(key.toLowerCase()) &&
      /\d{3,}/.test(val) &&
      !val.includes("http")
    ) {
      const cleaned = val.split("/")[0].trim();
      action = {type:"phone", label:`Call ${label}`, value:cleaned};
    }

    if (action) {
      const sig = `${action.type}:${action.value}`;
      if (!seen.has(sig)) {
        seen.add(sig);
        actions.push(action);
      }
    }
  }

  Object.values(value).forEach(v => findOfficialActions(v, actions, seen));
  return actions;
}

function renderActionButtons(routing) {
  const actions = findOfficialActions(routing).slice(0, 8);

  let html = `<div class="action-row">`;

  actions.forEach(action => {
    if (action.type === "url") {
      html += `<a class="action-btn primary" href="${escapeHtml(action.value)}" target="_blank" rel="noopener noreferrer">${escapeHtml(action.label)} ↗</a>`;
    } else if (action.type === "email") {
      html += `<a class="action-btn" href="mailto:${escapeHtml(action.value)}">${escapeHtml(action.label)}</a>`;
    } else if (action.type === "phone") {
      const tel = action.value.replace(/[^\d+]/g,"");
      html += `<a class="action-btn" href="tel:${escapeHtml(tel)}">${escapeHtml(action.label)}</a>`;
    }
  });

  html += `<button class="action-btn gold prepare-draft-btn" type="button">Prepare complaint draft</button>`;
  html += `<button class="action-btn add-evidence-result-btn" type="button">＋ Add evidence</button>`;
  html += `</div>`;
  html += `<p class="portal-note">Official portals open in a new tab. HariMaga does not sign in for you or transfer uploaded files into another website automatically.</p>`;

  return html;
}

async function prepareComplaintDraft() {
  if (!originalText) return;

  const res = await fetch("/api/complaint-draft", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      text: originalText,
      answers,
      evidence_ids: evidenceItems.map(x => x.id),
      request_id: requestId
    })
  });

  const data = await res.json();
  if (!res.ok || !data.ok) {
    throw new Error(data.error || "Could not prepare complaint draft.");
  }

  draftSubject.value = data.draft.subject || "";
  draftBody.value = data.draft.body || "";
  draftModal.classList.remove("hidden");
}

function closeDraft() {
  draftModal.classList.add("hidden");
}


function renderRouted(data) {
  lastRoutingData = data;
  const r = data.routing || {};
  const cls = data.classification || {};
  const title = routeTitle(data);
  const authority = routeAuthority(r);
  const contacts = collectVerifiedChannels(r);
  const required = collectRequiredInfo(r);
  const steps = collectSteps(r);

  setStep(4);
  pendingField = null;
  clearChoices();

  let district = r.district || r.jurisdiction?.incident_district || r.jurisdiction?.origin_district || "";
  let jurisdiction = r.jurisdiction?.jurisdiction || r.route_type || "";

  let liveSources = [];
  if (Array.isArray(r.live_sources)) {
    liveSources = r.live_sources.map(x => `${x.label}: ${x.url}`);
  }

  let html = `
    <div class="msg-name">HariMaga Guide</div>
    <p>Route found. I kept the result limited to the verified information available in the HariMaga knowledge base.</p>
    <div class="classification-strip">
      <span class="route-badge">${escapeHtml(humanize(cls.label))}</span>
      <span class="route-badge">✓ Verified-first</span>
    </div>
    <div class="result-card">
      <div class="result-head">
        <h4>${escapeHtml(title)}</h4>
        <p>${escapeHtml(humanize(r.route_type || "official route"))}</p>
      </div>
      <div class="result-body">
        <div class="result-grid">
          ${authority ? `<div class="info-box"><span>Authority</span><strong>${escapeHtml(authority)}</strong></div>` : ""}
          ${district ? `<div class="info-box"><span>District / Area</span><strong>${escapeHtml(district)}</strong></div>` : ""}
          ${jurisdiction ? `<div class="info-box"><span>Routing basis</span><strong>${escapeHtml(humanize(jurisdiction))}</strong></div>` : ""}
          ${r.subtype_label ? `<div class="info-box"><span>Concern type</span><strong>${escapeHtml(r.subtype_label)}</strong></div>` : ""}
        </div>
        ${resultSection("What to do", steps)}
        ${resultSection("Verified contact / official channel", contacts, "verified-contact")}
        ${resultSection("Information to prepare", required)}
        ${resultSection("Official live warning sources", liveSources)}
        ${r.note ? `<div class="result-section"><h5>Note</h5><p>${escapeHtml(r.note)}</p></div>` : ""}
        ${r.time_note ? `<div class="result-section"><h5>Timing note</h5><p>${escapeHtml(r.time_note)}</p></div>` : ""}
        ${r.policy?.evidence_safety ? `<div class="result-section"><div class="safety-note">${escapeHtml(r.policy.evidence_safety)}</div></div>` : ""}
        ${r.safety ? `<div class="result-section"><div class="safety-note">${escapeHtml(r.safety)}</div></div>` : ""}
        <div class="result-section">
          <h5>Next action</h5>
          ${renderActionButtons(r)}
        </div>
      </div>
    </div>`;

  const rendered = addMessage("assistant", html);
  rendered.querySelectorAll(".prepare-draft-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      try {
        await prepareComplaintDraft();
      } catch (err) {
        addMessage("assistant", `<div class="msg-name">HariMaga Guide</div><p>${escapeHtml(err.message)}</p>`);
      }
    });
  });
  rendered.querySelectorAll(".add-evidence-result-btn").forEach(btn => {
    btn.addEventListener("click", () => evidenceInput.click());
  });
  input.placeholder = "Describe another problem or click New request...";
}

async function apiRoute() {
  const res = await fetch("/api/route", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({text: originalText, answers})
  });

  const data = await res.json();
  if (!res.ok || !data.ok) throw new Error(data.error || "HariMaga API error");

  const r = data.routing || {};
  if (r.status === "needs_clarification") {
    renderClarification(r);
  } else if (r.status === "routed" || r.status === "resolved") {
    setStep(3);
    renderRouted(data);
  } else {
    pendingField = null;
    clearChoices();
    addMessage(
      "assistant",
      `<div class="msg-name">HariMaga Guide</div>
       <p>I couldn't safely finish this route.</p>
       <div class="result-card"><div class="result-body">
         <div class="safety-note">${escapeHtml(r.message || r.status || "Unknown routing state")}</div>
       </div></div>`
    );
  }
}

async function startRequest(text) {
  originalText = text.trim();
  if (!originalText) return;

  answers = {};
  pendingField = null;
  clearChoices();
  setStep(1);

  addMessage("user", `<p>${escapeHtml(originalText)}</p>`);
  const loading = addMessage(
    "assistant",
    `<div class="msg-name">HariMaga Guide</div><p>Understanding the issue and checking the safest routing path…</p>`
  );

  try {
    await apiRoute();
    loading.remove();
  } catch (err) {
    loading.remove();
    addMessage(
      "assistant",
      `<div class="msg-name">HariMaga Guide</div>
       <p>Backend error: ${escapeHtml(err.message)}</p>`
    );
  }
}

async function submitClarification(value, label=null) {
  if (!pendingField) return;
  answers[pendingField] = value;
  addMessage("user", `<p>${escapeHtml(label ?? value)}</p>`);
  pendingField = null;
  clearChoices();

  try {
    await apiRoute();
  } catch (err) {
    addMessage(
      "assistant",
      `<div class="msg-name">HariMaga Guide</div>
       <p>Backend error: ${escapeHtml(err.message)}</p>`
    );
  }
}

form.addEventListener("submit", async e => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  input.style.height = "auto";

  if (pendingField) await submitClarification(text);
  else await startRequest(text);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 110) + "px";
});

newBtn.addEventListener("click", async () => {
  clearPendingEvidence();

  for (const item of evidenceItems) {
    try {
      await fetch(`/api/evidence/${encodeURIComponent(item.id)}`, {
        method:"DELETE",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({request_id:requestId})
      });
    } catch {}
  }

  evidenceItems = [];
  requestId = newAnonymousRequestId();
  sessionStorage.setItem("harimaga_request_id", requestId);
  renderEvidenceTray();
  originalText = "";
  answers = {};
  pendingField = null;
  lastRoutingData = null;
  clearChoices();
  setStep(1);
  input.placeholder = "Type your problem here...";
  addMessage(
    "assistant",
    `<div class="msg-name">HariMaga Guide</div><p>New request started. Tell me the next problem.</p>`
  );
  input.focus();
});

promptButtons.forEach(btn => {
  btn.addEventListener("click", async () => {
    const prompt = btn.dataset.prompt || "";
    if (prompt) await startRequest(prompt);
  });
});

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (!data.ok || data.status !== "healthy") throw new Error();
    statusDot.className = "status-dot ok";
    backendStatus.textContent = data.evidence_storage
      ? `HariMaga connected · anonymous 24h evidence storage active`
      : `HariMaga backend connected · API Phase ${data.api_phase}`;
  } catch {
    statusDot.className = "status-dot bad";
    backendStatus.textContent = "HariMaga backend not connected";
  }
}

attachBtn.addEventListener("click", () => evidenceInput.click());
evidenceToolbarBtn.addEventListener("click", () => evidenceInput.click());

evidenceInput.addEventListener("change", () => {
  const files = [...evidenceInput.files];
  evidenceInput.value = "";

  if (!files.length) return;

  const remaining = Math.max(0, 6 - evidenceItems.length - pendingEvidence.length);

  files.slice(0, remaining).forEach(file => {
    if (file.size > 10 * 1024 * 1024) {
      addMessage(
        "assistant",
        `<div class="msg-name">HariMaga Guide</div><p>${escapeHtml(file.name)} is larger than 10 MB.</p>`
      );
      return;
    }

    pendingEvidence.push({
      file,
      previewUrl: file.type.startsWith("image/") ? URL.createObjectURL(file) : ""
    });
  });

  renderPendingEvidence();
});

sendEvidenceBtn.addEventListener("click", async () => {
  if (!pendingEvidence.length) return;

  attachBtn.classList.add("uploading");
  evidenceToolbarBtn.classList.add("uploading");
  sendEvidenceBtn.classList.add("uploading");

  evidenceUploadStatus.textContent = `Attaching ${pendingEvidence.length} file${pendingEvidence.length === 1 ? "" : "s"}…`;
  evidenceUploadStatus.className = "busy";

  const queue = [...pendingEvidence];
  const failed = [];

  for (const item of queue) {
    try {
      await uploadEvidenceFile(item.file);
      if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
    } catch (err) {
      failed.push(item);
      addMessage(
        "assistant",
        `<div class="msg-name">HariMaga Guide</div>
         <p>Could not attach <b>${escapeHtml(item.file.name)}</b>: ${escapeHtml(err.message)}</p>`
      );
    }
  }

  pendingEvidence = failed;
  attachBtn.classList.remove("uploading");
  evidenceToolbarBtn.classList.remove("uploading");
  sendEvidenceBtn.classList.remove("uploading");

  renderPendingEvidence();
  renderEvidenceTray();

  if (!failed.length && evidenceItems.length) {
    evidenceUploadStatus.textContent = `${evidenceItems.length} evidence file${evidenceItems.length === 1 ? "" : "s"} attached ✓`;
    evidenceUploadStatus.className = "ok";
  }
});

closeDraftBtn.addEventListener("click", closeDraft);
doneDraftBtn.addEventListener("click", closeDraft);
document.querySelectorAll("[data-close-draft]").forEach(el => el.addEventListener("click", closeDraft));

copyDraftBtn.addEventListener("click", async () => {
  const content = `${draftSubject.value}\n\n${draftBody.value}`;
  await navigator.clipboard.writeText(content);
  const old = copyDraftBtn.textContent;
  copyDraftBtn.textContent = "Copied ✓";
  setTimeout(() => copyDraftBtn.textContent = old, 1600);
});

restoreEvidenceForRequest();
checkHealth();
