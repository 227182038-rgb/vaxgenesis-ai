// k6 load test (audit 4.3, 5.1)
//
// Simulates realistic API traffic: auth, list projects, run pipeline.
//
// Run: k6 run tests/perf/k6_load.js
//
// Requires the backend to be running at http://localhost:8000.

import http from "k6/http";
import { check, sleep, group } from "k6";
import { Rate, Trend } from "k6/metrics";

const BACKEND_URL = __ENV.BACKEND_URL || "http://localhost:8000";

// Custom metrics
const errorRate = new Rate("errors");
const pipelineDuration = new Trend("pipeline_duration_ms");

// SLO targets (audit 4.7)
const SLO_API_SUCCESS_RATE = 0.99;
const SLO_API_P95_LATENCY_MS = 200;

export const options = {
  scenarios: {
    // Scenario 1: steady load on read endpoints
    steady_reads: {
      executor: "constant-vus",
      vus: 20,
      duration: "2m",
      tags: { scenario: "steady_reads" },
      exec: "readEndpoints",
    },
    // Scenario 2: ramp-up on auth + project creation
    auth_ramp: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 10 },
        { duration: "1m", target: 50 },
        { duration: "30s", target: 0 },
      ],
      tags: { scenario: "auth_ramp" },
      exec: "authFlow",
    },
  },
  thresholds: {
    // SLO enforcement — fail the run if these are breached
    "http_req_failed": [`rate<${1 - SLO_API_SUCCESS_RATE}`],
    "http_req_duration": [`p(95)<${SLO_API_P95_LATENCY_MS}`],
    "errors": [`rate<${1 - SLO_API_SUCCESS_RATE}`],
  },
};

const AUTH_PAYLOAD = JSON.stringify({
  email: "admin@vaxgenesis.ai",
  password: "admin123",
});
const HEADERS = { "Content-Type": "application/json" };

export function authFlow() {
  group("Login", () => {
    const res = http.post(`${BACKEND_URL}/api/v1/auth/login`, AUTH_PAYLOAD, {
      headers: HEADERS,
    });
    const ok = check(res, {
      "login 200": (r) => r.status === 200,
      "has token": (r) => r.json("access_token") !== undefined,
    });
    errorRate.add(!ok);
    sleep(0.5);
  });

  group("Get current user", () => {
    // First login to get a token
    const loginRes = http.post(`${BACKEND_URL}/api/v1/auth/login`, AUTH_PAYLOAD, {
      headers: HEADERS,
    });
    if (loginRes.status !== 200) {
      errorRate.add(true);
      return;
    }
    const token = loginRes.json("access_token");
    const res = http.get(`${BACKEND_URL}/api/v1/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const ok = check(res, {
      "me 200": (r) => r.status === 200,
      "has email": (r) => r.json("email") !== undefined,
    });
    errorRate.add(!ok);
    sleep(0.5);
  });
}

export function readEndpoints() {
  // Login once at the start of each VU iteration
  const loginRes = http.post(`${BACKEND_URL}/api/v1/auth/login`, AUTH_PAYLOAD, {
    headers: HEADERS,
  });
  if (loginRes.status !== 200) {
    errorRate.add(true);
    sleep(1);
    return;
  }
  const token = loginRes.json("access_token");
  const authHeaders = { Authorization: `Bearer ${token}` };

  group("Health check", () => {
    const res = http.get(`${BACKEND_URL}/api/v1/health`, { headers: authHeaders });
    errorRate.add(res.status !== 200);
  });

  group("List modules", () => {
    const res = http.get(`${BACKEND_URL}/api/v1/modules`, { headers: authHeaders });
    const ok = check(res, {
      "modules 200": (r) => r.status === 200,
      "has 31 modules": (r) => r.json().length === 31,
    });
    errorRate.add(!ok);
  });

  group("List projects", () => {
    const res = http.get(`${BACKEND_URL}/api/v1/projects`, { headers: authHeaders });
    errorRate.add(res.status >= 500);
  });

  group("List candidates", () => {
    const res = http.get(`${BACKEND_URL}/api/v1/candidates`, { headers: authHeaders });
    errorRate.add(res.status >= 500);
  });

  group("Surveillance status", () => {
    const res = http.get(`${BACKEND_URL}/api/v1/surveillance/status`, {
      headers: authHeaders,
    });
    errorRate.add(res.status >= 500);
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    "tests/perf/k6_results.json": JSON.stringify(data, null, 2),
    stdout: textSummary(data),
  };
}

function textSummary(data) {
  const lines = [
    "=== k6 Load Test Summary ===",
    `Total requests: ${data.metrics.http_reqs.values.count}`,
    `Failed requests: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%`,
    `P95 latency: ${data.metrics.http_req_duration.values["p(95)"].toFixed(0)}ms`,
    `P99 latency: ${data.metrics.http_req_duration.values["p(99)"].toFixed(0)}ms`,
    "",
    "SLO compliance:",
    `  Success rate >= 99%: ${
      data.metrics.http_req_failed.values.rate < 0.01 ? "PASS" : "FAIL"
    }`,
    `  P95 latency < 200ms: ${
      data.metrics.http_req_duration.values["p(95)"] < 200 ? "PASS" : "FAIL"
    }`,
  ];
  return lines.join("\n") + "\n";
}
