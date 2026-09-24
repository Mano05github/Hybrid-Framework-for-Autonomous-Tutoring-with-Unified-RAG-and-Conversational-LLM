# 15-Minute Canary Runbook (5%)

## Preconditions
1. Environment flags
- NEW_ARCH_ENABLED=1
- NEW_ARCH_FORCE_MODE=auto
- NEW_ARCH_CANARY_PERCENT=5
- VOICE_STREAMING_STT=1

2. Backend health
- python manage.py check
- python manage.py smoke_channels

## Test Script (15 minutes)
1. Minute 0-3: Basic flow
- Start one PBL session
- Send one text query
- Send one voice utterance
- Confirm turn state progression: listening -> transcribing -> reasoning -> speaking -> listening

2. Minute 3-7: Barge-in reliability
- Trigger AI response and interrupt mid-speech
- Immediately speak a new utterance
- Confirm no stale old response leaks after interruption

3. Minute 7-11: RAG and policy behavior
- Ask one concept question (expect possible RAG usage)
- Ask one implementation-progress question (expect likely no RAG)
- Check that responses remain Socratic (no direct full answer dump)

4. Minute 11-15: Stability pass
- Repeat 3-5 mixed turns quickly
- Watch reconnects/disconnects
- Confirm no hard failures in voice pipeline

## Metrics to Check
Use endpoint: /api/ai/stats/pbl-runtime/

1. counters
- arch_mode_new and arch_mode_legacy both increasing (mixed canary expected)
- interrupt_received increments when barge-in tested
- turn_completed increments steadily
- rag_used should be lower than rag_not_used in normal mixed tutoring

2. timing_avg_ms
- first_interim_latency
- first_text_latency
- first_audio_latency
- turn_total_latency

## Accept / Reject
Accept if:
1. No stale turn leakage observed
2. Interrupt works reliably in repeated tries
3. No major error spikes/disconnect loops
4. Latency remains stable across repeated turns

Reject and rollback if:
1. Frequent stale responses appear
2. Voice turns stall repeatedly
3. Error/disconnect rate spikes significantly

## Rollback
1. Set NEW_ARCH_FORCE_MODE=legacy
2. Restart backend
3. Verify basic session flow and voice interaction
