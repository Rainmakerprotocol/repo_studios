const DEFAULT_VIEW_LABEL = "Health · Screening Signal Timeline";

export function buildScreeningTimelineDiagram(history, options = {}) {
  const artifactLabel = options.artifactLabel ?? "CommandView Artifact";
  const viewLabel = options.viewLabel ?? DEFAULT_VIEW_LABEL;

  const events = Array.isArray(history?.events) ? history.events.filter(Boolean) : [];
  if (events.length === 0) {
    return {
      message: "No screening history events are recorded yet for this CommandView artifact.",
    };
  }

  const packSummaries = summarizeScreeningHistory(history);
  if (packSummaries.length === 0) {
    return {
      message: "Screening history is present but contains no per-pack events to render.",
    };
  }

  const lines = ["timeline"];
  lines.push(`  title ${formatTimelineText(`${artifactLabel} Screening Scores`)}`);

  packSummaries.forEach((summary) => {
    lines.push(`  section ${formatTimelineText(summary.label)}`);
    let previousEvent = null;
    summary.events.forEach((event) => {
      const timestampLabel = formatTimelineTimestamp(event?.timestamp);
      const eventLabel = formatScreeningTimelineEvent(event, previousEvent, timestampLabel);
      lines.push(`    ${timestampLabel} : ${formatTimelineText(eventLabel)}`);
      previousEvent = event;
    });
  });

  const packCount = packSummaries.length;
  const eventCount = events.length;
  const statusBuilder = typeof options.statusBuilder === "function" ? options.statusBuilder : null;
  const statusMessage = statusBuilder
    ? statusBuilder({ packCount, eventCount })
    : `Rendered screening timeline for ${packCount} pack${packCount === 1 ? "" : "s"} (${eventCount} event${eventCount === 1 ? "" : "s"}).`;

  return {
    definition: lines.join("\n"),
    label: viewLabel,
    statusMessage,
    packCount,
    eventCount,
  };
}

export function summarizeScreeningHistory(history) {
  if (!history) {
    return [];
  }

  const summaries = [];
  const packMap = history.packs instanceof Map ? history.packs : null;

  if (packMap) {
    packMap.forEach((entries, key) => {
      const events = Array.isArray(entries) ? entries.filter(Boolean) : [];
      if (events.length === 0) {
        return;
      }
      events.sort(compareEventsByTimestamp);
      const label = events[0]?.packLabel ?? key ?? "Screening Pack";
      summaries.push({ key, label, events });
    });
  } else {
    const regrouped = new Map();
    const events = Array.isArray(history.events) ? history.events.filter(Boolean) : [];
    events.forEach((event) => {
      const key = event && typeof event === "object"
        ? event.packId ?? event.packLabel ?? "unknown"
        : "unknown";
      const bucket = regrouped.get(key) ?? [];
      bucket.push(event);
      regrouped.set(key, bucket);
    });
    regrouped.forEach((bucket, key) => {
      const filtered = bucket.filter(Boolean);
      if (filtered.length === 0) {
        return;
      }
      filtered.sort(compareEventsByTimestamp);
      const label = filtered[0]?.packLabel ?? key ?? "Screening Pack";
      summaries.push({ key, label, events: filtered });
    });
  }

  summaries.sort((left, right) => {
    const leftLabel = String(left.label ?? "").toLowerCase();
    const rightLabel = String(right.label ?? "").toLowerCase();
    return leftLabel.localeCompare(rightLabel);
  });

  return summaries;
}

function compareEventsByTimestamp(left, right) {
  const leftTimestamp = left?.timestamp ?? "";
  const rightTimestamp = right?.timestamp ?? "";
  return String(leftTimestamp).localeCompare(String(rightTimestamp));
}

export function formatScreeningTimelineEvent(event, previousEvent, primaryMoment) {
  if (!event || typeof event !== "object") {
    return "No data";
  }

  const parts = [];
  parts.push(`[${formatSeverityLabel(event.severity)}]`);

  const scorePart = formatScoreValue(event.score);
  if (scorePart) {
    parts.push(scorePart);
  }

  const deltaPart = formatScoreDelta(event.score, previousEvent?.score);
  if (deltaPart) {
    parts.push(deltaPart);
  }

  const thresholdPart = formatThresholdSummary(event.thresholds);
  if (thresholdPart) {
    parts.push(thresholdPart);
  }

  const metricsPart = formatDocstringMetricsSummary(event.metrics);
  if (metricsPart) {
    parts.push(metricsPart);
  }

  const severityChange = formatSeverityTransition(event.severity, previousEvent?.severity);
  if (severityChange) {
    parts.push(severityChange);
  }

  const folderDetail = formatFolderChange(event.context, previousEvent?.context);
  if (folderDetail) {
    parts.push(folderDetail);
  }

  const inventoryMoment = formatInventoryMoment(event.context, primaryMoment);
  if (inventoryMoment) {
    parts.push(inventoryMoment);
  }

  const detail = parts.filter(Boolean).join(" · ");
  return detail || "No additional details";
}

export function formatTimelineTimestamp(rawTimestamp) {
  if (!rawTimestamp || typeof rawTimestamp !== "string") {
    return "Unknown";
  }
  const parsed = new Date(rawTimestamp);
  if (!Number.isNaN(parsed.getTime())) {
    const pad = (value) => String(value).padStart(2, "0");
    const year = parsed.getUTCFullYear();
    const month = pad(parsed.getUTCMonth() + 1);
    const day = pad(parsed.getUTCDate());
    const hour = pad(parsed.getUTCHours());
    const minute = pad(parsed.getUTCMinutes());
    return `${year}-${month}-${day} ${hour}h${minute}Z`;
  }
  return String(rawTimestamp).replace(/[:]/g, "").replace(/T/g, " ").trim() || "Unknown";
}

export function formatTimelineText(value) {
  if (value === null || value === undefined) {
    return "No data";
  }
  const text = String(value)
    .replace(/\s+/g, " ")
    .replace(/[:]/g, "")
    .trim();
  return text.length > 0 ? text : "No data";
}

export function formatSeverityLabel(rawSeverity) {
  const severity = typeof rawSeverity === "string" ? rawSeverity.toLowerCase() : "unknown";
  switch (severity) {
    case "ok":
      return "OK";
    case "warning":
      return "WARNING";
    case "critical":
      return "CRITICAL";
    default:
      return "UNKNOWN";
  }
}

export function formatScoreValue(rawScore) {
  const numeric = Number(rawScore);
  if (!Number.isFinite(numeric)) {
    return null;
  }
  const absoluteFraction = Math.abs(numeric % 1);
  const display = absoluteFraction < 0.05 ? numeric.toFixed(0) : numeric.toFixed(1);
  return `score ${display}`;
}

export function formatScoreDelta(currentScore, previousScore) {
  const current = Number(currentScore);
  const previous = Number(previousScore);
  if (!Number.isFinite(current) || !Number.isFinite(previous)) {
    return null;
  }
  const delta = current - previous;
  if (Math.abs(delta) < 0.05) {
    return null;
  }
  const absoluteFraction = Math.abs(delta % 1);
  const magnitude = absoluteFraction < 0.05 ? Math.round(delta) : Number(delta.toFixed(1));
  const prefix = delta > 0 ? "+" : "";
  return `delta ${prefix}${magnitude}`;
}

export function formatThresholdSummary(thresholds) {
  if (!thresholds || typeof thresholds !== "object") {
    return null;
  }
  const parts = [];
  if (Number.isFinite(Number(thresholds.warning))) {
    parts.push(`warn>=${formatNumericValue(thresholds.warning)}`);
  }
  if (Number.isFinite(Number(thresholds.failure))) {
    parts.push(`fail>=${formatNumericValue(thresholds.failure)}`);
  }
  if (parts.length === 0) {
    return null;
  }
  return `thresholds ${parts.join(" ")}`;
}

export function formatDocstringMetricsSummary(metrics) {
  if (!metrics || typeof metrics !== "object") {
    return null;
  }
  const total = Number(metrics.functions_total);
  const documented = Number(metrics.functions_documented);
  if (!Number.isFinite(total) || total <= 0 || !Number.isFinite(documented)) {
    return null;
  }
  const missingValue = Number.isFinite(Number(metrics.functions_missing))
    ? Number(metrics.functions_missing)
    : Math.max(total - documented, 0);

  let summary = `docs ${formatNumericValue(documented)}/${formatNumericValue(total)}`;
  if (Number.isFinite(missingValue) && missingValue > 0) {
    summary += ` missing ${formatNumericValue(missingValue)}`;
  }
  return summary;
}

export function formatSeverityTransition(currentSeverity, previousSeverity) {
  if (!previousSeverity) {
    return null;
  }
  const currentLabel = formatSeverityLabel(currentSeverity);
  const previousLabel = formatSeverityLabel(previousSeverity);
  if (currentLabel === previousLabel) {
    return null;
  }
  return `severity changed from ${previousLabel}`;
}

export function formatFolderChange(context, previousContext) {
  const folder = context && typeof context.folder_name === "string" ? context.folder_name.trim() : "";
  if (!folder) {
    return null;
  }
  const previousFolder = previousContext && typeof previousContext.folder_name === "string"
    ? previousContext.folder_name.trim()
    : "";
  if (folder === previousFolder) {
    return null;
  }
  return `folder ${folder}`;
}

export function formatInventoryMoment(context, primaryMoment) {
  if (!context || typeof context.inventory_generated_at !== "string") {
    return null;
  }
  const formatted = formatTimelineTimestamp(context.inventory_generated_at);
  if (!formatted || formatted === "Unknown" || formatted === primaryMoment) {
    return null;
  }
  return `inventory ${formatted}`;
}

export function formatNumericValue(rawValue) {
  const numeric = Number(rawValue);
  if (!Number.isFinite(numeric)) {
    return "-";
  }
  const absoluteFraction = Math.abs(numeric % 1);
  if (absoluteFraction < 0.05) {
    return String(Math.round(numeric));
  }
  return numeric.toFixed(1);
}

export const __test__ = {
  compareEventsByTimestamp,
};
