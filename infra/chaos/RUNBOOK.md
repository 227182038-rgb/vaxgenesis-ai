# Chaos Engineering Runbook (audit 5.5)

## Prerequisites

1. Chaos Mesh installed on the staging cluster:
   ```bash
   kubectl apply -f https://mirrors.chaos-mesh.org/chaos-mesh-v2.7.0.yaml
   ```

2. The VaxGenesis AI stack deployed and healthy.

3. A k6 load test running in the background to generate traffic during
   chaos injection:
   ```bash
   k6 run --vus 20 --duration 10m tests/perf/k6_load.js &
   ```

## Experiments

### Experiment 1: Pod kill (resilience to single-pod failure)

**Hypothesis:** Killing one backend pod does not cause 5xx errors
because HPA + multiple replicas absorb the loss.

```bash
kubectl apply -f infra/chaos/chaos-mesh.yaml
# Watch for 5xx in Prometheus:
#   rate(vaxgenesis_http_requests_total{status=~"5.."}[1m])
# Expected: 5xx rate stays below 1% during pod restart.
```

**Pass criteria:**
- 5xx error rate < 1% during the experiment
- HPA scales up to replace the killed pod within 60s
- No user-visible errors in the frontend

### Experiment 2: Network latency (resilience to slow DB)

**Hypothesis:** 200ms added latency between backend and postgres does
not cause request timeouts because SQLAlchemy connection pool + query
cache absorb the latency for cached queries.

**Pass criteria:**
- P95 latency stays below 500ms (slightly relaxed from 200ms SLO)
- No connection pool exhaustion
- Cache hit rate increases (more requests served from Redis)

### Experiment 3: Redis partition (graceful cache degradation)

**Hypothesis:** When Redis becomes unavailable, the backend degrades
gracefully to no-op caching (per `vaxgenesis/core/cache.py` design)
without errors.

**Pass criteria:**
- No 5xx errors
- P95 latency may increase but stays below 500ms (direct DB hits)
- Logs show `cache.redis_unavailable` warnings but no exceptions

## Schedule

- **Staging**: experiments run continuously via the cron schedule in
  `chaos-mesh.yaml` (every 5min / 1h / 6h respectively).
- **Production**: experiments are NEVER run automatically. Manual
  game-day exercises only, with on-call engineer present.

## Post-experiment

After each experiment:
1. Verify Grafana dashboards return to baseline within 5 minutes.
2. File any unexpected findings as GitHub issues labeled `chaos-finding`.
3. Update `docs/HIPAA_RISK_ANALYSIS.md` if a new threat is identified.
