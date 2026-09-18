import assert from "node:assert/strict";
import test from "node:test";
import {activityTrend, completionBreakdown, scoreTrend} from "../admin-charts.mjs";

test("completion breakdown does not exceed the number of views", () => {
  assert.deepEqual(completionBreakdown({views: 4, completed_sessions: 6}), {completed: 4, remaining: 0, rate: 100});
  assert.deepEqual(completionBreakdown({views: 0, completed_sessions: 0}), {completed: 0, remaining: 0, rate: 0});
});

test("score trend keeps completed scores chronological and on the 10-point scale", () => {
  assert.deepEqual(scoreTrend([
    {score: 12}, {session_id: "in-progress"}, {score: 7.5}, {score: -2},
  ]), [
    {label: "Phiên 1", value: 0}, {label: "Phiên 2", value: 7.5}, {label: "Phiên 3", value: 10},
  ]);
});

test("activity trend groups recent events and handles one timestamp", () => {
  const single = activityTrend([{timestamp: "2026-09-18T08:00:00Z"}, {timestamp: "2026-09-18T08:00:00Z"}]);
  assert.equal(single.length, 1);
  assert.equal(single[0].value, 2);

  const trend = activityTrend([
    {timestamp: "2026-09-18T08:00:00Z"}, {timestamp: "2026-09-18T08:02:00Z"}, {timestamp: "2026-09-18T08:04:00Z"},
  ], 3);
  assert.equal(trend.length, 3);
  assert.equal(trend.reduce((total, point) => total + point.value, 0), 3);
});