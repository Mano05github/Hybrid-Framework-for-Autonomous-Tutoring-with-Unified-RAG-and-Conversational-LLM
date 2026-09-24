"""
PBL WebSocket Consumer

URL: /ws/pbl/{session_id}/

Handles:
  canvas_snapshot   → run guide_node with image
  student_message   → run guide_node with text
  request_hint      → run hint_node
  submit_solution   → run evaluator_node + update mastery
  run_code          → run run_code_node
  telemetry_event   → batch-save TelemetryEvent rows
  idle_status       → log idle state
  interrupt         → cancel in-flight TTS task
    [binary frames]   → STT (Deepgram) → guide_node
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone as tz

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from langchain_core.messages import HumanMessage

from .pbl_graph import get_pbl_graph
from .live_contract import (
    TURN_INTERRUPTED,
    TURN_LISTENING,
    TURN_REASONING,
    TURN_SPEAKING,
    TURN_TRANSCRIBING,
)
from .policy_guard import apply_socratic_policy
from .runtime_metrics import incr as metrics_incr, timing as metrics_timing

logger = logging.getLogger(__name__)


VOICE_BARGE_IN = os.getenv('VOICE_BARGE_IN', '1') == '1'
VOICE_STREAMING_STT = os.getenv('VOICE_STREAMING_STT', '0') == '1'
PBL_POLICY_GUARD_ENABLED = os.getenv('PBL_POLICY_GUARD_ENABLED', '1') == '1'


class PBLConsumer(AsyncWebsocketConsumer):

    # ── Connection ────────────────────────────────────────────────────────────

    async def connect(self):
        self.session_id   = self.scope['url_route']['kwargs']['session_id']
        self.user         = self.scope.get('user')
        self._tts_task    = None
        self._stop_event  = asyncio.Event()
        self._pbl_session = None
        self._voice_context = {
            'canvas_state': None,
            'current_code': '',
            'time_since_last_action': 0.0,
            'problem_statement': '',
            'problem_title': '',
            'updated_at': time.time(),
        }
        self._turn_seq = 0
        self._active_turn_id = None
        self._turn_state = TURN_LISTENING
        self._voice_stream_turn_id = None
        self._voice_stream_chunks = []
        self._voice_stream_bytes = 0
        self._interim_task = None
        self._last_interim_text = ''
        self._turn_started_at = {}
        self._turn_first_interim_sent = set()
        self._arch_mode = _select_arch_mode(
            session_id=self.session_id,
            enabled=settings.NEW_ARCH_ENABLED,
            force_mode=settings.NEW_ARCH_FORCE_MODE,
            canary_percent=settings.NEW_ARCH_CANARY_PERCENT,
        )

        # Load PBLSession from DB
        try:
            self._pbl_session = await self._get_pbl_session(self.session_id)
        except Exception as exc:
            logger.error('[PBLConsumer] Session load error: %s', exc)
            await self.close(code=4004)
            return

        if self._pbl_session is None:
            logger.warning('[PBLConsumer] Unknown session %s', self.session_id)
            await self.close(code=4004)
            return

        await self.accept()
        logger.info('[PBLConsumer] Connected: session=%s user=%s', self.session_id,
                    getattr(self.user, 'id', 'anon'))
        metrics_incr('pbl_ws_connected')
        metrics_incr(f'arch_mode_{self._arch_mode}')
        await self._send_state_sync()

    async def disconnect(self, close_code):
        if self._tts_task and not self._tts_task.done():
            self._tts_task.cancel()
        if self._interim_task and not self._interim_task.done():
            self._interim_task.cancel()
        metrics_incr('pbl_ws_disconnected')
        logger.info('[PBLConsumer] Disconnected: %s (code=%s)', self.session_id, close_code)

    # ── Receive ───────────────────────────────────────────────────────────────

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            if self._arch_mode == 'new' and VOICE_STREAMING_STT and self._voice_stream_turn_id:
                await self._on_voice_chunk(bytes_data)
            else:
                # Legacy mode: single binary utterance
                await self._handle_audio(bytes_data)
            return

        if not text_data:
            return

        try:
            msg = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error('Invalid JSON')
            return

        msg_type = msg.get('type', '')
        payload  = msg.get('payload', msg)  # older clients send payload at top-level
        if isinstance(payload, dict):
            payload.setdefault('turn_id', msg.get('turn_id') or payload.get('turn_id'))

        handlers = {
            'canvas_snapshot': self._on_canvas_snapshot,
            'student_message': self._on_student_message,
            'voice_context':   self._on_voice_context,
            'voice_start':     self._on_voice_start,
            'voice_end':       self._on_voice_end,
            'request_hint':    self._on_hint_request,
            'submit_solution': self._on_submit,
            'run_code':        self._on_run_code,
            'telemetry_event': self._on_telemetry,
            'idle_status':     self._on_idle,
            'interrupt':       self._on_interrupt,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(payload)
        else:
            logger.debug('[PBLConsumer] Unhandled message type: %s', msg_type)

    # ── Message handlers ──────────────────────────────────────────────────────

    async def _on_canvas_snapshot(self, payload: dict):
        image_b64 = payload.get('image', '')
        trigger   = payload.get('trigger', 'auto')

        if trigger == 'auto':
            # Passive auto-snapshots: run guide silently (no response unless hint needed)
            return

        state = self._base_state()
        state.update({
            'message_type':  'canvas',
            'canvas_snapshot': image_b64,
            'messages': [HumanMessage(content='[Canvas snapshot sent for analysis]')],
        })
        await self._run_graph(state)

    async def _on_student_message(self, payload: dict):
        text = payload.get('message', '').strip()
        if not text:
            return
        turn_id = payload.get('turn_id') or self._new_turn_id('message')
        self._active_turn_id = turn_id
        self._turn_state = TURN_REASONING
        await self._send_state_sync(turn_id=turn_id)
        cached_ctx = self._latest_voice_context()

        current_code = payload.get('current_code')
        if current_code is None:
            current_code = cached_ctx.get('current_code', '')

        canvas_state = payload.get('canvas_state')
        if canvas_state is None:
            canvas_state = cached_ctx.get('canvas_state')

        time_idle = payload.get('time_since_last_action')
        if time_idle is None:
            time_idle = payload.get('time_since_last_action_seconds')
        if time_idle is None:
            time_idle = cached_ctx.get('time_since_last_action', 0.0)

        progress_state = self._infer_progress_state(
            canvas_state=canvas_state,
            current_code=current_code,
            attempt_count=getattr(self._pbl_session, 'attempt_count', 0),
            time_since_last_action=float(time_idle or 0.0),
        )

        state = self._base_state()
        state.update({
            'turn_id': turn_id,
            'message_type': 'message',
            'canvas_snapshot': None,
            'current_code': current_code or '',
            'canvas_state': canvas_state,
            'time_since_last_action': float(time_idle or 0.0),
            'progress_state': progress_state,
            'messages': [HumanMessage(content=text)],
        })

        # ── Socratic mode injection ───────────────────────────────────────────
        # Runs for both text messages AND voice (voice routes through here after STT)
        try:
            sess         = self._pbl_session
            canvas_state = state.get('canvas_state')
            time_idle    = float(state.get('time_since_last_action', 0))
            is_solved    = getattr(sess, 'is_solved', False)
            code         = state.get('current_code', '') or ''
            if code:
                state['current_code'] = code

            from ai_engine.cognitive_state_detector import get_cognitive_detector
            from ai_engine.socratic_mode_engine import get_socratic_engine

            struggle = get_cognitive_detector().detect(
                canvas_state,
                state.get('current_code', ''),
                sess.attempt_count,
                text,
                time_idle,
                is_solved,
            )
            decision = get_socratic_engine().decide_mode(
                is_solved,
                sess.attempt_count,
                sess.hint_count,
                time_idle,
                struggle,
            )
            state['teaching_hint'] = decision.teaching_hint
            state['struggle_type'] = struggle.type
            logger.info('[PBLConsumer] Socratic mode=%s struggle=%s', decision.mode, struggle.type)
        except Exception as exc:
            logger.warning('[PBLConsumer] Socratic injection error (non-fatal): %s', exc)
        # ─────────────────────────────────────────────────────────────────────

        await self._run_graph(state)

    async def _on_voice_context(self, payload: dict):
        if not isinstance(payload, dict):
            return

        try:
            time_idle = payload.get('time_since_last_action')
            if time_idle is None:
                time_idle = payload.get('time_since_last_action_seconds')

            self._voice_context = {
                'canvas_state': payload.get('canvas_state'),
                'current_code': payload.get('current_code', '') or '',
                'time_since_last_action': float(time_idle or 0.0),
                'problem_statement': payload.get('problem_statement', '') or '',
                'problem_title': payload.get('problem_title', '') or '',
                'updated_at': time.time(),
            }
        except Exception as exc:
            logger.warning('[PBLConsumer] voice_context parse error (non-fatal): %s', exc)

    async def _on_hint_request(self, payload: dict):
        hint_num = payload.get('hint_number', 1)
        code     = payload.get('current_code', '')

        await self._update_hint_count()

        state = self._base_state()
        state.update({
            'message_type': 'hint',
            'hint_number':  hint_num,
            'current_code': code,
            'messages': [HumanMessage(content='[Hint requested]')],
        })
        await self._run_graph(state)

    async def _on_voice_start(self, payload: dict):
        if self._arch_mode != 'new':
            return
        turn_id = payload.get('turn_id') or self._new_turn_id('voice')
        self._voice_stream_turn_id = turn_id
        self._voice_stream_chunks = []
        self._voice_stream_bytes = 0
        self._last_interim_text = ''
        self._active_turn_id = turn_id
        self._turn_state = TURN_TRANSCRIBING
        self._turn_started_at[turn_id] = time.perf_counter()
        metrics_incr('voice_turn_started')
        await self._send_state_sync(turn_id=turn_id)

    async def _on_voice_chunk(self, audio_chunk: bytes):
        if not audio_chunk or not self._voice_stream_turn_id:
            return
        self._voice_stream_chunks.append(bytes(audio_chunk))
        self._voice_stream_bytes += len(audio_chunk)

        # Emit best-effort interim transcript periodically without blocking ingest.
        if self._voice_stream_bytes >= 12000:
            if not self._interim_task or self._interim_task.done():
                turn_id = self._voice_stream_turn_id
                self._interim_task = asyncio.create_task(self._emit_interim_transcript(turn_id))

    async def _on_voice_end(self, payload: dict):
        if self._arch_mode != 'new':
            return
        turn_id = payload.get('turn_id') or self._voice_stream_turn_id or self._new_turn_id('voice')

        if self._interim_task and not self._interim_task.done():
            self._interim_task.cancel()

        audio_bytes = b''.join(self._voice_stream_chunks)
        self._voice_stream_turn_id = None
        self._voice_stream_chunks = []
        self._voice_stream_bytes = 0

        if not audio_bytes:
            self._turn_state = TURN_LISTENING
            await self._send_state_sync(turn_id=turn_id)
            return

        await self._transcribe_and_route(turn_id, audio_bytes)

    async def _on_submit(self, payload: dict):
        code        = payload.get('code', '').strip()
        attempt_num = payload.get('attempt_number', 1)

        if not code:
            await self._send_error('No code to evaluate.')
            return

        await self._increment_attempt_count()

        state = self._base_state()
        state.update({
            'message_type':  'submit',
            'current_code':  code,
            'canvas_snapshot': payload.get('canvas_snapshot'),
            'messages': [HumanMessage(content=f'[Submit attempt #{attempt_num}]')],
        })

        result = await self._run_graph(state, return_result=True)

        # Update mastery
        if result:
            code_result = result.get('code_result') or {}
            is_correct  = code_result.get('success', False)
            mastery_data = await self._update_mastery(is_correct, code)
            if mastery_data:
                await self.send(text_data=json.dumps({
                    'type': 'mastery_update',
                    **mastery_data,
                }))
                if mastery_data.get('session_end'):
                    await self.send(text_data=json.dumps({
                        'type': 'session_end',
                        'summary': True,
                    }))

    async def _on_run_code(self, payload: dict):
        code = payload.get('code', '').strip()
        if not code:
            await self._send_error('No code to run.')
            return
        state = self._base_state()
        state.update({
            'message_type': 'run_code',
            'current_code': code,
            'messages': [],
        })
        await self._run_graph(state)

    async def _on_telemetry(self, payload: dict):
        events = payload.get('events', [])
        if events:
            await self._save_telemetry(events)

    async def _on_idle(self, payload: dict):
        idle = payload.get('idle', False)
        logger.debug('[PBLConsumer] idle_status=%s session=%s', idle, self.session_id)

    async def _on_interrupt(self, payload: dict):
        """Cancel in-flight TTS streaming."""
        if not VOICE_BARGE_IN:
            return
        metrics_incr('interrupt_received')
        self._stop_event.set()
        if self._tts_task and not self._tts_task.done():
            self._tts_task.cancel()
        self._stop_event.clear()
        self._turn_state = TURN_INTERRUPTED
        self._voice_stream_turn_id = None
        self._voice_stream_chunks = []
        self._voice_stream_bytes = 0
        if self._interim_task and not self._interim_task.done():
            self._interim_task.cancel()
        await self._send_state_sync(turn_id=payload.get('turn_id') if isinstance(payload, dict) else None)
        logger.info('[PBLConsumer] TTS interrupted')

    async def _handle_audio(self, audio_bytes: bytes):
        """STT via Deepgram → route as student_message."""
        turn_id = self._new_turn_id('voice')
        await self._transcribe_and_route(turn_id, audio_bytes)

    async def _transcribe_and_route(self, turn_id: str, audio_bytes: bytes):
        self._active_turn_id = turn_id
        self._turn_state = TURN_TRANSCRIBING
        await self._send_state_sync(turn_id=turn_id)
        stt_t0 = time.perf_counter()
        try:
            text = await asyncio.get_event_loop().run_in_executor(
                None, self._stt_sync, audio_bytes
            )
            metrics_timing('stt_latency', (time.perf_counter() - stt_t0) * 1000)
            if text:
                await self.send(text_data=json.dumps({
                    'type': 'final_transcript',
                    'turn_id': turn_id,
                    'text': text,
                }))
                hydrated_payload = {
                    'message': text,
                    'turn_id': turn_id,
                }
                hydrated_payload.update(self._latest_voice_context())
                await self._on_student_message(hydrated_payload)
            else:
                self._turn_state = TURN_LISTENING
                await self._send_state_sync(turn_id=turn_id)
        except Exception as exc:
            logger.error('[PBLConsumer] STT error: %s', exc)
            self._turn_state = TURN_LISTENING
            await self._send_state_sync(turn_id=turn_id)

    async def _emit_interim_transcript(self, turn_id: str):
        # Snapshot current stream bytes for non-blocking best-effort interim STT.
        if turn_id != self._voice_stream_turn_id:
            return
        audio_bytes = b''.join(self._voice_stream_chunks)
        if len(audio_bytes) < 6000:
            return
        try:
            text = await asyncio.get_event_loop().run_in_executor(None, self._stt_sync, audio_bytes)
            text = (text or '').strip()
            if text and text != self._last_interim_text and turn_id == self._voice_stream_turn_id:
                self._last_interim_text = text
                if turn_id in self._turn_started_at and turn_id not in self._turn_first_interim_sent:
                    elapsed = (time.perf_counter() - self._turn_started_at[turn_id]) * 1000
                    metrics_timing('first_interim_latency', elapsed)
                    self._turn_first_interim_sent.add(turn_id)
                await self.send(text_data=json.dumps({
                    'type': 'interim_transcript',
                    'turn_id': turn_id,
                    'text': text,
                }))
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.debug('[PBLConsumer] interim STT skipped: %s', exc)

    # ── Graph execution ───────────────────────────────────────────────────────

    def _base_state(self) -> dict:
        session = self._pbl_session
        return {
            'session_id':         str(session.id),
            'turn_id':            self._active_turn_id,
            'user_id':            str(getattr(self.user, 'id', 'anon')),
            'topic_id':           getattr(getattr(session, 'concept', None), 'topic_id', None),
            'concept_name':       session.concept.topic.title if session.concept else '',
            'problem_title':      session.problem_title,
            'problem_statement':  session.problem_statement,
            'difficulty':         session.difficulty_level,
            'hint_number':        session.hint_count,
            'attempt_count':      session.attempt_count,
            'mastery_score':      session.mastery_score,
            'current_code':       '',
            'canvas_snapshot':    None,
            'messages':           [],
            'user_emotion':       None,
            'canvas_state':       None,
            'time_since_last_action': 0.0,
            'progress_state':     None,
            # Socratic fields — defaults; overwritten by _on_student_message injection
            'teaching_hint':      None,
            'struggle_type':      None,
        }

    def _latest_voice_context(self) -> dict:
        ctx = self._voice_context or {}
        # If context is stale, still return fields but keep values conservative.
        # We use best-effort context rather than dropping voice requests.
        return {
            'canvas_state': ctx.get('canvas_state'),
            'current_code': ctx.get('current_code', ''),
            'time_since_last_action': float(ctx.get('time_since_last_action', 0.0) or 0.0),
        }

    def _infer_progress_state(
        self,
        canvas_state: dict,
        current_code: str,
        attempt_count: int,
        time_since_last_action: float,
    ) -> str:
        code = (current_code or '').strip()
        has_code = bool(code)

        blocks = (canvas_state or {}).get('text_blocks') or []
        drawings = (canvas_state or {}).get('drawings') or []
        notes = (canvas_state or {}).get('notes') or []
        has_canvas = bool(blocks or drawings or notes)

        if not has_code and not has_canvas and attempt_count == 0:
            return 'not_started'

        if time_since_last_action >= 30:
            return 'stuck'

        if has_code and ('return ' in code or 'print(' in code or 'def ' in code):
            if attempt_count >= 1:
                return 'almost_done'

        if has_code and (('for ' in code) or ('while ' in code) or ('if ' in code)):
            return 'in_progress'

        if has_code or has_canvas:
            return 'started'

        return 'stuck'

    async def _run_graph(self, state: dict, return_result: bool = False):
        """Run the PBL LangGraph in a thread pool and stream results to client."""
        turn_id = state.get('turn_id') or self._active_turn_id
        self._turn_state = TURN_REASONING
        await self._send_state_sync(turn_id=turn_id)
        await self._send_typing(True)
        graph_t0 = time.perf_counter()

        try:
            graph  = get_pbl_graph()
            result = await asyncio.get_event_loop().run_in_executor(
                None, graph.invoke, state
            )
            metrics_timing('graph_latency', (time.perf_counter() - graph_t0) * 1000)
        except Exception as exc:
            logger.error('[PBLConsumer] Graph error: %s', exc, exc_info=True)
            await self._send_typing(False)
            await self._send_error('AI processing error.')
            return None

        await self._send_typing(False)

        # ── Dispatch results to client ────────────────────────────────────

        # If a newer turn replaced this one (or it was interrupted), do not emit stale output.
        if self._is_stale_turn(turn_id):
            logger.info('[PBLConsumer] Dropping stale turn output: %s', turn_id)
            if return_result:
                return result
            return None

        # code_result (run_code / evaluate)
        code_result = result.get('code_result')
        if code_result:
            await self.send(text_data=json.dumps({
                'type': 'code_result',
                **code_result,
            }))

        # highlight overlay
        highlight = result.get('highlight')
        if highlight:
            await self.send(text_data=json.dumps({
                'type': 'highlight',
                **highlight,
            }))

        # AI voice (text + audio)
        response_text  = result.get('response_text', '')
        response_audio = result.get('response_audio', b'')
        if result.get('rag_used'):
            metrics_incr('rag_used')
        else:
            metrics_incr('rag_not_used')

        policy_meta = {'blocked': False, 'reason': None}
        if PBL_POLICY_GUARD_ENABLED and response_text:
            policy = apply_socratic_policy(
                response_text,
                struggle_type=state.get('struggle_type'),
            )
            response_text = policy.text
            policy_meta = {'blocked': policy.blocked, 'reason': policy.reason}
            if policy.blocked:
                metrics_incr('policy_blocked')
                if policy.reason:
                    metrics_incr(f'policy_block_reason_{policy.reason}')

        if response_text:
            if turn_id in self._turn_started_at:
                metrics_timing('first_text_latency', (time.perf_counter() - self._turn_started_at[turn_id]) * 1000)
            await self.send(text_data=json.dumps({
                'type': 'ai_text_delta',
                'turn_id': turn_id,
                'text': response_text,
                'is_final': True,
                'policy': policy_meta,
            }))
            await self.send(text_data=json.dumps({
                'type':      'ai_voice',
                'turn_id':   turn_id,
                'transcript': response_text,
                'policy': policy_meta,
            }))

        if response_audio:
            # Stream audio as binary frames
            self._stop_event.clear()
            self._turn_state = TURN_SPEAKING
            await self._send_state_sync(turn_id=turn_id)
            if turn_id in self._turn_started_at:
                metrics_timing('first_audio_latency', (time.perf_counter() - self._turn_started_at[turn_id]) * 1000)
            self._tts_task = asyncio.create_task(
                self._stream_audio(response_audio)
            )
            await self._tts_task

        self._turn_state = TURN_LISTENING
        await self._send_state_sync(turn_id=turn_id)
        metrics_incr('turn_completed')
        if turn_id in self._turn_started_at:
            metrics_timing('turn_total_latency', (time.perf_counter() - self._turn_started_at[turn_id]) * 1000)
            self._turn_started_at.pop(turn_id, None)
        self._turn_first_interim_sent.discard(turn_id)

        if return_result:
            return result
        return None

    async def _stream_audio(self, audio_bytes: bytes):
        """Send audio in 4KB chunks so the client can start playing immediately."""
        CHUNK = 4096
        try:
            for i in range(0, len(audio_bytes), CHUNK):
                if self._stop_event.is_set():
                    break
                await self.send(bytes_data=audio_bytes[i:i + CHUNK])
                await asyncio.sleep(0)   # yield to event loop
        except asyncio.CancelledError:
            logger.debug('[PBLConsumer] Audio streaming cancelled')

    # ── DB helpers ────────────────────────────────────────────────────────────

    @database_sync_to_async
    def _get_pbl_session(self, session_id):
        from ai_engine.pbl.models import PBLSession
        return PBLSession.objects.select_related(
            'concept__topic__subject', 'subject', 'user'
        ).filter(pk=session_id, status='active').first()

    @database_sync_to_async
    def _update_hint_count(self):
        from ai_engine.pbl.models import PBLSession
        PBLSession.objects.filter(pk=self.session_id).update(
            hint_count=models_F('hint_count') + 1
        )
        if self._pbl_session:
            self._pbl_session.hint_count += 1

    @database_sync_to_async
    def _increment_attempt_count(self):
        from ai_engine.pbl.models import PBLSession
        PBLSession.objects.filter(pk=self.session_id).update(
            attempt_count=models_F('attempt_count') + 1
        )
        if self._pbl_session:
            self._pbl_session.attempt_count += 1

    @database_sync_to_async
    def _update_mastery(self, is_correct: bool, code: str) -> dict:
        from ai_engine.pbl.models import PBLSession, PBLAttempt
        from ai_engine.pbl.adaptive_engine import update_mastery
        from django.utils import timezone

        session = PBLSession.objects.select_related('concept').get(pk=self.session_id)

        # Save attempt record
        attempt = PBLAttempt.objects.create(
            session=session,
            attempt_number=session.attempt_count,
            code_submitted=code,
            is_correct=is_correct,
        )

        # Compute mastery delta
        result = update_mastery(session, attempt)
        session.save()

        # Optionally mark session complete
        if result.get('session_end'):
            session.status   = 'completed'
            session.ended_at = timezone.now()
            session.save()

        # Update in-memory reference
        if self._pbl_session:
            self._pbl_session.mastery_score    = session.mastery_score
            self._pbl_session.difficulty_level = session.difficulty_level

        return result

    @database_sync_to_async
    def _save_telemetry(self, events: list):
        from ai_engine.pbl.models import TelemetryEvent, PBLSession
        import uuid
        try:
            session = PBLSession.objects.get(pk=self.session_id)
        except Exception:
            session = None

        objs = []
        for ev in events:
            ts_raw = ev.get('timestamp') or ev.get('ts')
            try:
                ts = datetime.fromisoformat(ts_raw.replace('Z', '+00:00')) if ts_raw else datetime.now(tz.utc)
            except Exception:
                ts = datetime.now(tz.utc)
            objs.append(TelemetryEvent(
                session=session,
                event_type=ev.get('event_type', 'unknown'),
                payload={k: v for k, v in ev.items() if k not in ('event_type', 'timestamp')},
                ts=ts,
            ))
        TelemetryEvent.objects.bulk_create(objs, ignore_conflicts=True)

    # ── Utility helpers ────────────────────────────────────────────────────────

    def _stt_sync(self, audio_bytes: bytes) -> str:
        """Synchronous STT call (runs in executor). Uses Gemini Flash STT."""
        try:
            from ai_engine.stt import get_stt_engine
            text = get_stt_engine().transcribe_audio(audio_bytes)
            # transcribe_audio already returns None for noise/silence
            return text or ''
        except Exception as exc:
            logger.error('[PBLConsumer] STT sync error: %s', exc)
            return ''

    async def _send_error(self, message: str):
        await self.send(text_data=json.dumps({'type': 'error', 'message': message}))

    async def _send_typing(self, visible: bool):
        await self.send(text_data=json.dumps(
            {'type': 'typing_start' if visible else 'typing_stop'}
        ))

    async def _send_state_sync(self, turn_id: str = None):
        await self.send(text_data=json.dumps({
            'type': 'state_sync',
            'session_id': self.session_id,
            'turn_id': turn_id or self._active_turn_id,
            'turn_state': self._turn_state,
            'arch_mode': self._arch_mode,
        }))

    def _new_turn_id(self, source: str) -> str:
        self._turn_seq += 1
        return f'{self.session_id}:{source}:{self._turn_seq}'

    def _is_stale_turn(self, turn_id: str) -> bool:
        if not turn_id:
            return False
        if self._turn_state == TURN_INTERRUPTED:
            return True
        return bool(self._active_turn_id and self._active_turn_id != turn_id)


def _select_arch_mode(
    session_id: str,
    enabled: bool,
    force_mode: str,
    canary_percent: int,
) -> str:
    if not enabled:
        return 'legacy'

    mode = (force_mode or 'auto').lower()
    if mode in ('legacy', 'new'):
        return mode

    pct = max(0, min(100, int(canary_percent or 0)))
    if pct >= 100:
        return 'new'
    if pct <= 0:
        return 'legacy'

    # Stable deterministic bucket by session id.
    bucket = int(hashlib.sha256((session_id or '').encode('utf-8')).hexdigest()[:8], 16) % 100
    return 'new' if bucket < pct else 'legacy'


# ── F() import deferred to avoid circular at module load ─────────────────────
from django.db.models import F as models_F
