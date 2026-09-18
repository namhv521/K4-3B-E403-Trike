function number(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

export function completionBreakdown(report) {
  const views = Math.max(0, number(report?.views));
  const completed = Math.min(views, Math.max(0, number(report?.completed_sessions)));
  return {completed, remaining: views - completed, rate: views ? Math.round((completed / views) * 100) : 0};
}

export function scoreTrend(sessions, limit = 8) {
  return (Array.isArray(sessions) ? sessions : [])
    .filter((session) => typeof session.score === "number" && Number.isFinite(session.score))
    .slice(0, limit)
    .reverse()
    .map((session, index) => ({label: `Phiên ${index + 1}`, value: Math.max(0, Math.min(10, session.score))}));
}

export function activityTrend(events, buckets = 6) {
  const validEvents = (Array.isArray(events) ? events : [])
    .map((event) => new Date(event.timestamp).getTime())
    .filter(Number.isFinite)
    .sort((left, right) => left - right);
  if (!validEvents.length) return [];

  const count = Math.max(1, Math.min(buckets, validEvents.length));
  const start = validEvents[0];
  const end = validEvents.at(-1);
  if (start === end) return [{label: new Date(start).toLocaleTimeString("vi-VN", {hour: "2-digit", minute: "2-digit", hour12: false}), value: validEvents.length}];

  const width = (end - start) / count;
  return Array.from({length: count}, (_, index) => {
    const lower = start + index * width;
    const upper = index === count - 1 ? end : lower + width;
    const value = validEvents.filter((timestamp) => timestamp >= lower && (index === count - 1 ? timestamp <= upper : timestamp < upper)).length;
    return {
      label: new Date(lower).toLocaleTimeString("vi-VN", {hour: "2-digit", minute: "2-digit", hour12: false}),
      value,
    };
  });
}