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

const helpTexts = {
  baseline: "从线上系统或内部主数据导出的基准表，用于作为比对和关联基础。至少需要 FE编号、云服务、需求标题。",
  sourceFiles: "专项、服务或临时维护的需求列表。可以上传多份，系统会按 FE/RR/云服务关联。",
  feColumn: "内部 Feature 编号字段名。如果表头不是 FE编号，可以改成实际列名。",
  rrColumn: "外部需求编号字段名。客户或外部系统提出的需求通常需要填写 RR。",
  serviceColumn: "需求承载的云服务字段名。用于区分服务视角和专项视角，缺失会被标记为异常。",
  titleColumn: "需求标题字段名，用于页面展示、人工确认和导出阅读。",
  ownedServices: "用逗号填写你负责的服务，例如 A,B。大小写不敏感，用于生成“我负责的云服务需求”视图。",
  commentFields: "这些字段会被拼进待回刷评论。例如：对齐结论、会议纪要、风险。未选择的扩展字段仍会导出。",
  fillDefaults: "当某些列为空或缺失时，可以显式配置默认值。例如 {\"云服务\":\"A\"}。原始数据仍会保留。",
  commentTarget: "选择评论最终写到 FE、RR，还是 FE 和 RR 都写。回刷前仍需要人工确认。",
  syncLinked: "开启后，评论会同步给直接关联的 FE/RR，但不会继续递归扩散。",
  preview: "这里展示 FE/RR/云服务关联后的在线结果。黄色、橙色、红色分别表示提醒、高优先级异常和严重异常。",
  commentTemplate: "用于生成回刷评论的文本格式。支持 {{FE编号}}、{{RR编号}}、{{对齐结论}} 等变量。",
};

const form = document.querySelector("#job-form");
const button = document.querySelector("#submit-button");
const formStatus = document.querySelector("#form-status");
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
const helpPopover = document.querySelector("#help-popover");

let currentPayload = null;
let previewRows = [];
let isSubmitting = false;

initTemplates();
initHelp();
updateSubmitState();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const validation = validateForm();
  if (!validation.valid) {
    showError({
      code: "FORM_REQUIRED_FIELDS_MISSING",
      message: `还有必填项未完成：${validation.missing.join("、")}。`,
      suggestion: "请先补齐标注“必填”的项目，然后再开始分析。",
    });
    updateSubmitState();
    return;
  }

  isSubmitting = true;
  button.disabled = true;
  button.textContent = "分析中...";

  try {
    const data = new FormData(form);
    data.set("comment_template", templateText.value || DEFAULT_TEMPLATE);
    data.set("sync_linked", data.get("sync_linked") === "on" ? "true" : "false");

    const response = await fetch("/api/jobs", { method: "POST", body: data });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw normalizeApiError(payload);
    }

    currentPayload = payload;
    previewRows = payload.preview_rows || [];
    renderSummary(payload.summary || {});
    renderFilters(payload.filters || {});
    renderPreview();
    renderDownloads(payload.downloads || {});
  } catch (error) {
    showError(error);
  } finally {
    isSubmitting = false;
    button.textContent = "开始分析";
    updateSubmitState();
  }
});

[serviceFilter, severityFilter, ownedFilter, searchBox].forEach((element) => {
  element.addEventListener("input", renderPreview);
});

form.addEventListener("input", updateSubmitState);
form.addEventListener("change", updateSubmitState);

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
    ["多来源共同管理", summary.multi_source_count],
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

function validateForm() {
  const missing = [];
  form.querySelectorAll("[required][data-required-label]").forEach((element) => {
    const label = element.dataset.requiredLabel || "必填项";
    if (element.type === "file") {
      if (!element.files || element.files.length === 0) {
        missing.push(label);
      }
      return;
    }
    if (!String(element.value || "").trim()) {
      missing.push(label);
    }
  });
  return { valid: missing.length === 0, missing };
}

function updateSubmitState() {
  const validation = validateForm();
  button.disabled = isSubmitting || !validation.valid;
  if (isSubmitting) {
    formStatus.textContent = "正在分析，请稍候。";
    formStatus.classList.remove("ready");
    return;
  }
  if (validation.valid) {
    formStatus.textContent = "必填项已完成，可以开始分析。";
    formStatus.classList.add("ready");
    return;
  }
  formStatus.textContent = `请完成以下页面必填项：${validation.missing.join("、")}。Excel 内部字段会在分析时继续校验。`;
  formStatus.classList.remove("ready");
}

function initHelp() {
  document.querySelectorAll(".help-trigger").forEach((button) => {
    const text = helpTexts[button.dataset.help] || "暂无说明。";
    button.setAttribute("title", text);
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleHelp(button, text);
    });
    button.addEventListener("mouseenter", () => showHelp(button, text));
    button.addEventListener("mouseleave", hideHelp);
  });
  document.addEventListener("click", hideHelp);
}

function toggleHelp(anchor, text) {
  if (!helpPopover.classList.contains("hidden") && helpPopover.dataset.anchor === anchor.dataset.help) {
    hideHelp();
    return;
  }
  showHelp(anchor, text);
}

function showHelp(anchor, text) {
  const rect = anchor.getBoundingClientRect();
  helpPopover.textContent = text;
  helpPopover.dataset.anchor = anchor.dataset.help;
  helpPopover.style.left = `${Math.min(rect.left, window.innerWidth - 340)}px`;
  helpPopover.style.top = `${rect.bottom + window.scrollY + 8}px`;
  helpPopover.classList.remove("hidden");
}

function hideHelp() {
  helpPopover.classList.add("hidden");
  helpPopover.removeAttribute("data-anchor");
}

function normalizeApiError(payload) {
  const detail = payload.detail;
  if (detail && typeof detail === "object") {
    return {
      message: detail.message || "分析失败。",
      suggestion: detail.suggestion || "请检查上传文件和页面配置后重试。",
      code: detail.code || "UNKNOWN_ERROR",
    };
  }
  return {
    message: typeof detail === "string" ? detail : "分析失败。",
    suggestion: "请检查上传文件和页面配置后重试。",
    code: "UNKNOWN_ERROR",
  };
}

function showError(error) {
  const payload = typeof error === "object" ? error : { message: String(error) };
  errorBox.innerHTML = `
    <strong>${escapeHtml(payload.message || "分析失败。")}</strong>
    ${payload.suggestion ? `<p>${escapeHtml(payload.suggestion)}</p>` : ""}
    ${payload.code ? `<small>错误码：${escapeHtml(payload.code)}</small>` : ""}
  `;
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
