const DEFAULT_TEMPLATE = `【需求对齐结论】
来源列表：{{来源列表}}
云服务：{{云服务}}
关联FE：{{FE编号}}
关联RR：{{RR编号}}
对齐时间：{{对齐时间}}
对齐对象：{{对齐对象}}

【对齐结论】
{{对齐结论}}

【补充信息】
{{补充信息}}

【回刷说明】
本评论由需求列表关联工具根据用户确认结果生成。`;

const form = document.querySelector("#job-form");
const button = document.querySelector("#submit-button");
const errorBox = document.querySelector("#error");
const summaryPanel = document.querySelector("#summary-panel");
const filtersPanel = document.querySelector("#filters");
const previewPanel = document.querySelector("#preview-panel");
const previewBody = document.querySelector("#preview-table tbody");
const serviceFilter = document.querySelector("#service-filter");
const severityFilter = document.querySelector("#severity-filter");
const ownedFilter = document.querySelector("#owned-filter");
const searchBox = document.querySelector("#search-box");
const detailBox = document.querySelector("#detail");
const packageLink = document.querySelector("#package-link");
const jsonLink = document.querySelector("#json-link");
const templateSelect = document.querySelector("#template-select");
const templateName = document.querySelector("#template-name");
const templateText = document.querySelector("#comment-template");
const saveTemplateButton = document.querySelector("#save-template");
const deleteTemplateButton = document.querySelector("#delete-template");
const resetTemplateButton = document.querySelector("#reset-template");

let currentPayload = null;
let previewRows = [];

initTemplates();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  button.disabled = true;
  button.textContent = "分析中...";

  try {
    const data = new FormData(form);
    data.set("comment_template", templateText.value || DEFAULT_TEMPLATE);
    data.set("sync_linked", data.get("sync_linked") === "on" ? "true" : "false");

    const response = await fetch("/api/jobs", { method: "POST", body: data });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "分析失败");
    }

    currentPayload = payload;
    previewRows = payload.preview_rows || [];
    renderSummary(payload.summary);
    renderFilters(payload.filters || {});
    renderPreview();
    renderDownloads(payload.downloads || {});
  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "开始分析";
  }
});

[serviceFilter, severityFilter, ownedFilter, searchBox].forEach((element) => {
  element.addEventListener("input", renderPreview);
});

saveTemplateButton.addEventListener("click", () => {
  const templates = loadTemplates();
  const id = templateSelect.value || crypto.randomUUID();
  templates[id] = { id, name: templateName.value || "未命名模板", content: templateText.value || DEFAULT_TEMPLATE };
  saveTemplates(templates);
  renderTemplateSelect(id);
});

deleteTemplateButton.addEventListener("click", () => {
  const id = templateSelect.value;
  if (id === "default") return;
  const templates = loadTemplates();
  delete templates[id];
  saveTemplates(templates);
  renderTemplateSelect("default");
});

resetTemplateButton.addEventListener("click", () => {
  templateName.value = "默认需求对齐模板";
  templateText.value = DEFAULT_TEMPLATE;
});

templateSelect.addEventListener("change", () => {
  const templates = loadTemplates();
  const selected = templates[templateSelect.value] || templates.default;
  templateName.value = selected.name;
  templateText.value = selected.content;
});

function renderSummary(summary) {
  const cards = [
    ["FE总数", summary.fe_count],
    ["RR总数", summary.rr_count],
    ["云服务数", summary.service_count],
    ["来源列表数", summary.source_list_count],
    ["待建FE", summary.pending_fe_count],
    ["FE候选", summary.candidate_fe_count],
    ["多来源", summary.multi_source_count],
    ["待回刷评论", summary.sync_comment_count],
  ];
  summaryPanel.innerHTML = cards.map(([label, value]) => `<div><strong>${value ?? 0}</strong><span>${label}</span></div>`).join("");
  summaryPanel.classList.remove("hidden");
}

function renderFilters(filters) {
  fillSelect(serviceFilter, ["", ...(filters.services || [])], "全部");
  fillSelect(severityFilter, ["", ...(filters.severities || [])], "全部");
  filtersPanel.classList.remove("hidden");
}

function fillSelect(select, values, emptyLabel) {
  select.innerHTML = "";
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value || emptyLabel;
    select.appendChild(option);
  });
}

function renderPreview() {
  const serviceValue = serviceFilter.value;
  const severityValue = severityFilter.value;
  const ownedValue = ownedFilter.value;
  const query = searchBox.value.trim().toLowerCase();

  const rows = previewRows.filter((row) => {
    if (serviceValue && !row.service.includes(serviceValue)) return false;
    if (severityValue && row.severity !== severityValue) return false;
    if (ownedValue && row.owned !== ownedValue) return false;
    if (query) {
      const haystack = `${row.fe_id} ${row.rr_id} ${row.title}`.toLowerCase();
      if (!haystack.includes(query)) return false;
    }
    return true;
  });

  previewBody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.className = severityClass(row.severity);
    tr.innerHTML = `
      <td>${escapeHtml(row.fe_id)}</td>
      <td>${escapeHtml(row.rr_id)}</td>
      <td>${escapeHtml(row.service)}</td>
      <td>${escapeHtml(row.source)}</td>
      <td>${escapeHtml(row.title)}</td>
      <td>${escapeHtml(row.owned)}</td>
      <td>${escapeHtml(row.relation)}</td>
      <td>${escapeHtml(row.issue)}</td>
    `;
    tr.addEventListener("click", () => renderDetail(row));
    previewBody.appendChild(tr);
  });
  previewPanel.classList.remove("hidden");
}

function renderDetail(row) {
  detailBox.className = "";
  detailBox.innerHTML = `
    <dl>
      <dt>FE</dt><dd>${escapeHtml(row.fe_id || "-")}</dd>
      <dt>RR</dt><dd>${escapeHtml(row.rr_id || "-")}</dd>
      <dt>云服务</dt><dd>${escapeHtml(row.service || "-")}</dd>
      <dt>来源列表</dt><dd>${escapeHtml(row.source || "-")}</dd>
      <dt>是否归我负责</dt><dd>${escapeHtml(row.owned)}</dd>
      <dt>关系</dt><dd>${escapeHtml(row.relation)}</dd>
      <dt>异常</dt><dd>${escapeHtml(row.issue)}</dd>
    </dl>
    <h3>来源列表扩展摘要</h3>
    <pre>${escapeHtml(row.extension_summary || "无")}</pre>
  `;
}

function renderDownloads(downloads) {
  packageLink.href = downloads.package || "#";
  packageLink.classList.toggle("hidden", !downloads.package);
  jsonLink.href = downloads.sync_plan_json || "#";
  jsonLink.classList.toggle("hidden", !downloads.sync_plan_json);
}

function severityClass(severity) {
  if (severity === "严重") return "row-critical";
  if (severity === "高优先级异常") return "row-high";
  if (severity === "提醒") return "row-warning";
  return "";
}

function initTemplates() {
  const templates = loadTemplates();
  if (!templates.default) {
    templates.default = { id: "default", name: "默认需求对齐模板", content: DEFAULT_TEMPLATE };
    saveTemplates(templates);
  }
  renderTemplateSelect("default");
}

function loadTemplates() {
  try {
    return JSON.parse(localStorage.getItem("commentTemplates") || "{}");
  } catch {
    return {};
  }
}

function saveTemplates(templates) {
  localStorage.setItem("commentTemplates", JSON.stringify(templates));
}

function renderTemplateSelect(selectedId) {
  const templates = loadTemplates();
  templateSelect.innerHTML = "";
  Object.values(templates).forEach((template) => {
    const option = document.createElement("option");
    option.value = template.id;
    option.textContent = template.name;
    templateSelect.appendChild(option);
  });
  templateSelect.value = selectedId;
  const selected = templates[selectedId] || templates.default;
  templateName.value = selected.name;
  templateText.value = selected.content;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
