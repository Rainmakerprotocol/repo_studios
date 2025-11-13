const DEFAULT_VIEW_LABEL = "Risk & Assurance · Git Churn Risk Map";
const DEFAULT_CENTER_LABEL = "Git Churn Risk Map";
const DEFAULT_MODULE_LIMIT = 8;

export function buildGitChurnRiskMapDiagram(modules, options = {}) {
  const modulesMap = toMap(modules);
  if (!modulesMap || modulesMap.size === 0) {
    return {
      message: options.missingModulesMessage ?? "No modules recorded in this CommandView artifact.",
    };
  }

  const functionsMap = toMap(options.functions) ?? null;
  const baselines = normalizeBaselines(options.baselines);

  const summaries = buildModuleSummaries(modulesMap, {
    functions: functionsMap,
    baselines,
  });

  if (summaries.length === 0) {
    return {
      message: options.emptyMessage ?? "No git churn metrics recorded for the selected scope.",
    };
  }

  summaries.sort(compareModuleSummaries);

  const moduleLimit = resolvePositiveInteger(options.moduleLimit, DEFAULT_MODULE_LIMIT);
  const selectedSummaries = summaries.slice(0, moduleLimit);

  resetMermaidIdCounter();
  const lines = ["graph TD"];
  appendClassDefinitions(lines);

  const centerLabelRaw = typeof options.centerLabel === "string" && options.centerLabel.trim().length > 0
    ? options.centerLabel.trim()
    : DEFAULT_CENTER_LABEL;
  const centerId = sanitizeMermaidId(options.centerId ?? "git_churn_center");
  lines.push(`  ${centerId}["${escapeMermaidLabel(centerLabelRaw)}"]`);

  selectedSummaries.forEach((summary) => {
    const nodeId = sanitizeMermaidId(`module_${summary.moduleId}`);
    lines.push(`  ${nodeId}["${escapeMermaidLabel(buildModuleLabel(summary))}"]`);
    lines.push(`  ${centerId} --> ${nodeId}`);
    lines.push(`  class ${nodeId} ${resolveSeverityClass(summary.severity)};`);
  });

  const stats = buildStatsSnapshot({
    allSummaries: summaries,
    displayedSummaries: selectedSummaries,
    moduleLimit,
    baselines,
  });

  const statusMessage = buildStatusMessage(stats, {
    scopeDescription: options.scopeDescription,
    fallbackNotice: options.fallbackNotice,
  });

  return {
    definition: lines.join("\n"),
    label: options.viewLabel ?? DEFAULT_VIEW_LABEL,
    statusMessage,
    statusDetails: selectedSummaries.map((summary) => buildStatusDetail(summary)),
    stats,
  };
}

function buildModuleSummaries(modulesMap, context) {
  const summaries = [];
  modulesMap.forEach((moduleRecord, identifier) => {
    const summary = createModuleSummary(identifier, moduleRecord, context);
    if (summary) {
      summaries.push(summary);
    }
  });
  return summaries;
}

function createModuleSummary(identifier, moduleRecord, context) {
  if (!moduleRecord || typeof moduleRecord !== "object") {
    return null;
  }

  const churn = moduleRecord.gitChurn ?? moduleRecord.git_churn ?? null;
  if (!churn || typeof churn !== "object") {
    return null;
  }

  const commits = normalizeNonNegativeNumber(churn.commit_count);
  const additions = normalizeNonNegativeNumber(churn.additions);
  const deletions = normalizeNonNegativeNumber(churn.deletions);
  const netChanges = normalizeNumber(churn.net_changes);
  const linesChanged = additions + deletions;

  if (commits === 0 && linesChanged === 0 && !Number.isFinite(netChanges)) {
    return null;
  }

  const baselines = context?.baselines ?? normalizeBaselines();
  const coverageAverage = computeCoverageAverage(moduleRecord, context?.functions, identifier);

  const commitRatio = baselines.averageCommits > 0
    ? commits / baselines.averageCommits
    : commits > 0
      ? Number.POSITIVE_INFINITY
      : 0;
  const lineRatio = baselines.averageLinesChanged > 0
    ? linesChanged / baselines.averageLinesChanged
    : linesChanged > 0
      ? Number.POSITIVE_INFINITY
      : 0;
  const netRatio = baselines.averageNetChanges > 0
    ? Math.abs(netChanges) / baselines.averageNetChanges
    : Number.isFinite(netChanges) && netChanges !== 0
      ? Number.POSITIVE_INFINITY
      : 0;

  const severityScore = Math.max(commitRatio, lineRatio, netRatio);
  const severity = classifySeverity(severityScore, commits, linesChanged);

  return {
    moduleId: identifier,
    displayName: moduleRecord.moduleId ?? identifier,
    churn,
    commits,
    additions,
    deletions,
    netChanges: Number.isFinite(netChanges) ? netChanges : null,
    linesChanged,
    severity,
    severityScore,
    coverageAverage,
    latestCommit: churn.latest_commit ?? null,
  };
}

function compareModuleSummaries(left, right) {
  const severityRank = {
    critical: 0,
    high: 1,
    moderate: 2,
    observed: 3,
    stable: 4,
  };
  const leftRank = severityRank[left?.severity] ?? 5;
  const rightRank = severityRank[right?.severity] ?? 5;
  if (leftRank !== rightRank) {
    return leftRank - rightRank;
  }
  if ((right?.linesChanged ?? 0) !== (left?.linesChanged ?? 0)) {
    return (right?.linesChanged ?? 0) - (left?.linesChanged ?? 0);
  }
  if ((right?.commits ?? 0) !== (left?.commits ?? 0)) {
    return (right?.commits ?? 0) - (left?.commits ?? 0);
  }
  return (left?.moduleId ?? "").localeCompare(right?.moduleId ?? "");
}

function classifySeverity(score, commits, linesChanged) {
  const commitCount = Number.isFinite(commits) ? commits : 0;
  const lineTotal = Number.isFinite(linesChanged) ? linesChanged : 0;

  if (!Number.isFinite(score)) {
    return commitCount > 0 || lineTotal > 0 ? "critical" : "stable";
  }
  if (score >= 4 || commitCount >= 20 || lineTotal >= 2000) {
    return "critical";
  }
  if (score >= 2.5 || commitCount >= 12 || lineTotal >= 800) {
    return "high";
  }
  if (score >= 1.25 || commitCount >= 6 || lineTotal >= 300) {
    return "moderate";
  }
  if (score > 0 || commitCount > 0 || lineTotal > 0) {
    return "observed";
  }
  return "stable";
}

function buildModuleLabel(summary) {
  const lines = [];
  const name = summary.displayName ?? summary.moduleId;
  lines.push(name);
  lines.push(`Risk ${formatSeverityLabel(summary.severity)}`);
  lines.push(`Commits ${summary.commits}`);
  const net = formatNetChange(summary.netChanges);
  lines.push(`Δ +${summary.additions}/-${summary.deletions} (net ${net})`);
  lines.push(`Lines changed ${summary.linesChanged}`);
  if (summary.coverageAverage !== null) {
    lines.push(`Coverage ${formatCoveragePercent(summary.coverageAverage)}`);
  }
  if (summary.latestCommit && typeof summary.latestCommit === "object") {
    const timestamp = summary.latestCommit.timestamp ?? null;
    if (typeof timestamp === "string" && timestamp.length > 0) {
      lines.push(`Latest ${formatTimestampLabel(timestamp)}`);
    }
  }
  return lines.join("\n");
}

function buildStatsSnapshot(payload) {
  const allSummaries = Array.isArray(payload.allSummaries) ? payload.allSummaries : [];
  const displayedSummaries = Array.isArray(payload.displayedSummaries) ? payload.displayedSummaries : [];
  const moduleLimit = resolvePositiveInteger(payload.moduleLimit, DEFAULT_MODULE_LIMIT);
  const baselines = normalizeBaselines(payload.baselines);

  let totalCommits = 0;
  let totalLinesChanged = 0;

  allSummaries.forEach((summary) => {
    totalCommits += summary.commits;
    totalLinesChanged += summary.linesChanged;
  });

  const counts = {
    critical: 0,
    high: 0,
    moderate: 0,
    observed: 0,
    stable: 0,
  };

  const commitValues = [];
  const lineValues = [];

  displayedSummaries.forEach((summary) => {
    counts[summary.severity] = (counts[summary.severity] ?? 0) + 1;
    commitValues.push(summary.commits);
    lineValues.push(summary.linesChanged);
  });

  const medianCommits = commitValues.length > 0 ? computeMedian(commitValues) : 0;
  const medianLinesChanged = lineValues.length > 0 ? computeMedian(lineValues) : 0;

  return {
    moduleCount: allSummaries.length,
    displayedModules: displayedSummaries.length,
    moduleLimit,
    totalCommits,
    totalLinesChanged,
    medianCommits,
    medianLinesChanged,
    baselines,
    ...counts,
  };
}

function buildStatusMessage(stats, options) {
  const scope = typeof options?.scopeDescription === "string" && options.scopeDescription.trim().length > 0
    ? ` for ${options.scopeDescription.trim()}`
    : "";
  const baselineSnippet = stats.baselines.averageCommits > 0
    ? `baseline commits ${formatNumber(stats.baselines.averageCommits)} / Δ ${formatNumber(stats.baselines.averageLinesChanged)}`
    : "baseline unknown";
  let message = `Rendered Git Churn Risk Map${scope} (modules ${stats.displayedModules}/${stats.moduleCount}, critical ${stats.critical}, high ${stats.high}, moderate ${stats.moderate}, median commits ${formatNumber(stats.medianCommits)}, median Δ ${formatNumber(stats.medianLinesChanged)}, ${baselineSnippet}).`;
  if (options?.fallbackNotice) {
    message = `${message} ${options.fallbackNotice}`;
  }
  return message;
}

function buildStatusDetail(summary) {
  return {
    type: "module-summary",
    title: summary.displayName ?? summary.moduleId,
    severity: summary.severity,
    commits: summary.commits,
    additions: summary.additions,
    deletions: summary.deletions,
    netChanges: summary.netChanges,
    linesChanged: summary.linesChanged,
    coverageAverage: summary.coverageAverage,
    latestCommitHash: summary.latestCommit?.hash ?? null,
    latestCommitTimestamp: summary.latestCommit?.timestamp ?? null,
  };
}

function appendClassDefinitions(lines) {
  lines.push("  classDef churnCritical fill:#7f1d1d,stroke:#f87171,color:#fee2e2,stroke-width:2.5px;");
  lines.push("  classDef churnHigh fill:#78350f,stroke:#f59e0b,color:#fff7ed,stroke-width:2px;");
  lines.push("  classDef churnModerate fill:#1f2937,stroke:#facc15,color:#fef9c3,stroke-width:1.8px;");
  lines.push("  classDef churnObserved fill:#0f172a,stroke:#38bdf8,color:#e0f2fe,stroke-width:1.5px;");
  lines.push("  classDef churnStable fill:#0f172a,stroke:#4ade80,color:#dcfce7,stroke-width:1.3px;");
}

function resolveSeverityClass(severity) {
  switch (severity) {
    case "critical":
      return "churnCritical";
    case "high":
      return "churnHigh";
    case "moderate":
      return "churnModerate";
    case "observed":
      return "churnObserved";
    default:
      return "churnStable";
  }
}

function computeCoverageAverage(moduleRecord, functionsMap, identifier) {
  if (!(functionsMap instanceof Map)) {
    return null;
  }
  const functionIds = Array.isArray(moduleRecord?.functions) ? moduleRecord.functions : [];
  const coverageValues = [];
  functionIds.forEach((functionId) => {
    const fn = functionsMap.get(functionId);
    const value = resolveCoverageValueFromFunction(fn);
    if (value !== null) {
      coverageValues.push(value);
    }
  });
  if (coverageValues.length === 0) {
    return null;
  }
  const total = coverageValues.reduce((sum, value) => sum + value, 0);
  return total / coverageValues.length;
}

function resolveCoverageValueFromFunction(fn) {
  if (!fn || typeof fn !== "object") {
    return null;
  }
  if (Number.isFinite(fn.metrics?.coverage)) {
    return normalizeCoverageValue(fn.metrics.coverage);
  }
  if (Number.isFinite(fn.coverage)) {
    return normalizeCoverageValue(fn.coverage);
  }
  return null;
}

function normalizeCoverageValue(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return null;
  }
  if (numeric <= 0) {
    return 0;
  }
  if (numeric > 1) {
    if (numeric <= 100) {
      return Math.min(1, Math.max(0, numeric / 100));
    }
    return Math.min(1, Math.max(0, numeric));
  }
  return Math.min(1, Math.max(0, numeric));
}

function normalizeBaselines(raw) {
  const candidate = raw && typeof raw === "object" ? raw : {};
  const filesWithDataRaw = Number(candidate.files_with_data ?? candidate.filesWithData);
  const filesWithData = Number.isFinite(filesWithDataRaw) && filesWithDataRaw > 0 ? filesWithDataRaw : 0;
  const totalCommitsRaw = Number(candidate.total_commits ?? candidate.totalCommits);
  const totalCommits = Number.isFinite(totalCommitsRaw) && totalCommitsRaw > 0 ? totalCommitsRaw : 0;
  const totalAdditionsRaw = Number(candidate.total_additions ?? candidate.totalAdditions);
  const totalAdditions = Number.isFinite(totalAdditionsRaw) && totalAdditionsRaw > 0 ? totalAdditionsRaw : 0;
  const totalDeletionsRaw = Number(candidate.total_deletions ?? candidate.totalDeletions);
  const totalDeletions = Number.isFinite(totalDeletionsRaw) && totalDeletionsRaw > 0 ? totalDeletionsRaw : 0;
  const netChangesRaw = Number(candidate.net_changes ?? candidate.netChanges);
  const netChanges = Number.isFinite(netChangesRaw) ? netChangesRaw : 0;

  const files = filesWithData > 0 ? filesWithData : 0;
  const totalLinesChanged = totalAdditions + totalDeletions;
  const averageCommits = files > 0 ? totalCommits / files : 0;
  const averageLinesChanged = files > 0 ? totalLinesChanged / files : 0;
  const averageNetChanges = files > 0 ? Math.abs(netChanges) / files : 0;

  return {
    filesWithData,
    totalCommits,
    totalAdditions,
    totalDeletions,
    netChanges,
    totalLinesChanged,
    averageCommits,
    averageLinesChanged,
    averageNetChanges,
    latestCommit: candidate.latest_commit ?? candidate.latestCommit ?? null,
  };
}

function computeMedian(values) {
  const sorted = values.slice().sort((a, b) => a - b);
  const length = sorted.length;
  if (length === 0) {
    return 0;
  }
  const middle = Math.floor(length / 2);
  if (length % 2 === 0) {
    return (sorted[middle - 1] + sorted[middle]) / 2;
  }
  return sorted[middle];
}

function formatSeverityLabel(severity) {
  const value = typeof severity === "string" && severity.length > 0 ? severity : "stable";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatNetChange(value) {
  if (!Number.isFinite(value)) {
    return "0";
  }
  if (value > 0) {
    return `+${value}`;
  }
  return `${value}`;
}

function formatTimestampLabel(timestamp) {
  if (typeof timestamp !== "string" || timestamp.length === 0) {
    return "unknown";
  }
  const datePart = timestamp.split("T")[0];
  return datePart || timestamp;
}

function formatCoveragePercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "-";
  }
  if (numeric <= 1) {
    return `${Math.round(numeric * 100)}%`;
  }
  return `${Math.round(numeric)}%`;
}

function formatNumber(value) {
  if (!Number.isFinite(value)) {
    return "0";
  }
  if (Number.isInteger(value)) {
    return `${value}`;
  }
  return `${Math.round(value * 10) / 10}`;
}

function normalizeNonNegativeNumber(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return 0;
  }
  return Math.max(0, Math.floor(numeric));
}

function normalizeNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : Number.NaN;
}

function resolvePositiveInteger(value, fallback) {
  if (!Number.isFinite(Number(value))) {
    return fallback;
  }
  const numeric = Math.floor(Number(value));
  return numeric > 0 ? numeric : fallback;
}

function toMap(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Map) {
    return value;
  }
  if (Array.isArray(value)) {
    const map = new Map();
    value.forEach((entry, index) => {
      if (!entry || typeof entry !== "object") {
        return;
      }
      const key = entry.id ?? entry.moduleId ?? entry.module_id ?? String(index);
      map.set(key, entry);
    });
    return map;
  }
  if (typeof value === "object") {
    const map = new Map();
    Object.entries(value).forEach(([key, entry]) => {
      map.set(key, entry);
    });
    return map;
  }
  return null;
}

function escapeMermaidLabel(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/"/g, "'")
    .replace(/\n/g, "<br/>");
}

let mermaidIdCounter = 0;

function resetMermaidIdCounter() {
  mermaidIdCounter = 0;
}

function sanitizeMermaidId(value) {
  if (!value || typeof value !== "string") {
    mermaidIdCounter += 1;
    return `node_${mermaidIdCounter}`;
  }
  const sanitized = value.replace(/[^a-zA-Z0-9_]/g, "_");
  if (!sanitized) {
    mermaidIdCounter += 1;
    return `node_${mermaidIdCounter}`;
  }
  if (/^[0-9]/.test(sanitized)) {
    return `n_${sanitized}`;
  }
  return sanitized;
}

export const __test__ = {
  classifySeverity,
  buildModuleLabel,
  buildStatusMessage,
  normalizeBaselines,
  computeCoverageAverage,
  resolveSeverityClass,
};
