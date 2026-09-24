# Phase 4 Canary Rollout Checklist

## Goal
Safely migrate traffic from legacy flow to the new Gemini-Live + PBL architecture with fast rollback.

## Pre-Canary Gates
1. `python manage.py check` passes.
2. `python manage.py test ai_engine.tests` passes.
3. `python manage.py smoke_channels` passes.
4. Voice turn lifecycle verified manually: listening -> transcribing -> reasoning -> speaking -> listening.
5. Policy guard verified manually on at least one direct-answer-like prompt.
6. RAG gate verified manually for both retrieval and no-retrieval turns.

## Canary Stages
1. Stage A (5% sessions): enable new architecture and monitor 30-60 minutes.
2. Stage B (25% sessions): continue if no SLO breach.
3. Stage C (50% sessions): continue if quality and latency remain stable.
4. Stage D (100% sessions): full cutover with rollback kept available.

## Runtime Metrics to Watch
1. WebSocket disconnect rate.
2. First interim transcript latency.
3. First AI text delta latency.
4. First AI audio chunk latency.
5. Turn completion latency (p50 and p95).
6. Interrupt success rate.
7. Policy block rate and reason distribution.
8. RAG invocation rate.

## Abort Conditions
1. Error rate spikes above baseline by >2x.
2. p95 turn latency exceeds threshold for 10+ minutes.
3. Frequent stale-turn leakage observed.
4. Voice interrupts fail repeatedly.

## Rollback Procedure
1. Set `NEW_ARCH_ENABLED=0`.
2. Restart backend service.
3. Verify legacy websocket flow and AI response path.
4. Capture logs and incident notes.

## Post-Canary Signoff
1. Engineering signoff on reliability.
2. Product signoff on mentoring quality.
3. Teaching/pedagogy signoff on Socratic compliance.
4. Document final env flags used at cutover.
