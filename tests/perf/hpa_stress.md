# Performance & HPA Stress Test Runbook (audit 5.1, 5.3)

## Goal

Validate that the VaxGenesis AI backend scales horizontally under
load and that the HPA triggers correctly.

## Prerequisites

- A running Kubernetes cluster (or docker-compose for local validation)
- `k6` installed locally (`brew install k6` or `https://k6.io/docs/getting-started/installation/`)
- The backend deployed with HPA enabled (see `infra/k8s/backend.yaml`)

## Steps

### 1. Baseline measurement

```bash
# Single-VU warm-up to measure cold-start latency
k6 run --vus 1 --duration 30s tests/perf/k6_load.js
```

Record the baseline P95 latency.

### 2. Steady-state load (2 minutes, 20 VUs)

```bash
k6 run tests/perf/k6_load.js
```

Expected:
- `http_req_failed` rate < 1%
- P95 latency < 200ms (per SLO)
- `errors` rate < 1%

### 3. Ramp-up stress test

```bash
k6 run --scenario auth_ramp --vus 50 --duration 3m tests/perf/k6_load.js
```

While running, monitor:
```bash
kubectl get hpa -n vaxgenesis -w
kubectl top pods -n vaxgenesis
```

Expected:
- HPA scales backend from 3 → up to 20 replicas as CPU > 70%
- No 5xx errors during scaling events
- P99 latency stays below 1s

### 4. Sustained peak load (10 minutes, 100 VUs)

```bash
k6 run --vus 100 --duration 10m tests/perf/k6_load.js
```

Expected:
- All replicas saturated but stable
- Database connection pool not exhausted (max 20 + 10 overflow)
- Redis cache hit rate > 60% on read endpoints
- No OOM kills (`kubectl describe pod`)

### 5. Scale-down validation

After the load test ends:
```bash
# Wait 10 minutes for scale-down
sleep 600
kubectl get hpa -n vaxgenesis
```

Expected:
- HPA scales back down to `minReplicas: 3`
- No pods in CrashLoopBackOff

## Failure modes to watch for

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| 5xx spike during scale-up | DB connection pool exhaustion | Increase `pool_size` in `db/session.py` |
| P99 > 1s under load | Missing cache; add `@cached` decorator | Use `vaxgenesis.core.cache.cached` |
| HPA not triggering | Missing/incorrect resource requests | Check `resources.requests.cpu` in deployment |
| Pod OOM kills | Memory leak in long-running worker | Set `worker_max_tasks_per_child=100` (already configured) |
| Redis evicting keys | Cache too small | Increase `maxmemory` in Redis config |

## Reporting

After each run, attach:
- `tests/perf/k6_results.json` (auto-generated)
- `kubectl describe hpa -n vaxgenesis` output
- Grafana dashboard screenshot at peak load

To the release notes for the version under test.
