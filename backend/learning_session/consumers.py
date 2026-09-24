import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .orchestrator import SessionOrchestrator
from .tts_service import MossTTSService  # ElevenLabs TTS
import asyncio
import time
import logging
from ai_engine.visual_generator import VisualExplanationGenerator, should_generate_visual

logger = logging.getLogger(__name__)

# Store active orchestrators in memory (Simple dict for now, use Redis in Prod)
active_sessions = {}

# Store telemetry monitors for active sessions (Gap 5)
telemetry_monitors = {}


def _convert_canvas_command_to_dict(cmd):
    """
    Standardized conversion of CanvasCommand dataclass to dictionary.
    Handles all fields including optional ones with proper null-safety.
    
    Args:
        cmd: CanvasCommand dataclass instance
        
    Returns:
        dict: Serializable dictionary with all canvas command fields
    """
    return {
        'action': cmd.action,
        'content': cmd.content,
        'position': cmd.position,
        'style': cmd.style,
        'animate': cmd.animate,
        'duration': cmd.duration,
        'font': cmd.font,
        'color': cmd.color,
        'size': cmd.size,
        'pause_after': cmd.pause_after,
        'visual_stage': cmd.visual_stage,
        'concept_tag': cmd.concept_tag,
        'misconception_target': cmd.misconception_target,
        'attention_anchor': cmd.attention_anchor,
        'emotion': cmd.emotion,
        'focus_region': cmd.focus_region,
        'points': cmd.points,  # Already Optional, can be None
        'speech_sync_offset': cmd.speech_sync_offset
    }

class LearningSessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'session_{self.session_id}'
        self.telemetry_task = None  # Gap 5: Background telemetry streaming task
        self.last_activity_time = time.time()  # Gap 5: Track for pause detection
        user = self.scope.get('user')
        self.user_id = user.id if user and hasattr(user, 'id') else None

        # Initialize Orchestrator for this session if not exists
        if self.session_id not in active_sessions:
            active_sessions[self.session_id] = SessionOrchestrator(self.session_id)
        
        self.orchestrator = active_sessions[self.session_id]
        self.moss_tts = MossTTSService.get_instance()  # ElevenLabs TTS
        self.prev_render_mode = "default"  # v3: track mode transitions
        self.prev_session_phase = "diagnostic"  # v2: track phase transitions
        self.audio_stop_event = asyncio.Event()  # barge-in: set to interrupt TTS
        self._tts_task = None                     # barge-in: track streaming TTS task
        self.explanation_cursor = 0               # TTS resume: char offset in current text
        self._current_tts_text = ""               # TTS resume: full text of current TTS utterance
        
        # Gap 5: Initialize telemetry monitor
        from ai_engine.gaps.visionary_telemetry import LightweightTelemetryMonitor
        if self.session_id not in telemetry_monitors:
            telemetry_monitors[self.session_id] = LightweightTelemetryMonitor()
            # Start session tracking (user_id would come from auth context)
            telemetry_monitors[self.session_id].start_session(
                self.user_id or 'anonymous',
                self.session_id
            )
        
        self.telemetry_monitor = telemetry_monitors[self.session_id]

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Gap 5: Start background telemetry streaming (10s interval)
        self.telemetry_task = asyncio.create_task(self._stream_telemetry())

    async def disconnect(self, close_code):
        # Clean up MOSS TTS session
        if hasattr(self, 'moss_tts') and hasattr(self, 'session_id'):
            self.moss_tts.cleanup_session(self.session_id)
        
        # Gap 5: Stop telemetry streaming task
        if self.telemetry_task:
            self.telemetry_task.cancel()
            try:
                await self.telemetry_task
            except asyncio.CancelledError:
                pass
        
        # Gap 5: End telemetry session
        if hasattr(self, 'telemetry_monitor'):
            self.telemetry_monitor.end_session()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        from asgiref.sync import sync_to_async
        
        if bytes_data:
            import tempfile
            import os
            try:
                # 1. Use ElevenLabs STT (no credential file, auto-detects language)
                from ai_engine.stt import get_stt_engine
                
                # 2. Analyze Emotion (Async) — save to temp file for emotion only
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
                    temp_audio.write(bytes_data)
                    temp_path = temp_audio.name
                
                emotion_label = await sync_to_async(self.orchestrator.analyze_emotion)(temp_path)
                
                # 3. Transcribe with ElevenLabs Scribe v1 (no encoding param needed)
                stt_engine = get_stt_engine()
                user_text = await sync_to_async(stt_engine.transcribe_audio)(
                    audio_content=bytes_data
                )

                # 4. Cleanup temp file
                os.remove(temp_path)
                
                # 5. Process Conversation (if text found)
                if user_text:
                    print(f"User said: {user_text}")
                    
                    # Notify frontend immediately so user isn't left in silence
                    await self.send(text_data=json.dumps({
                        'type': 'thinking',
                        'message': '🤔 Thinking...',
                        'user_text': user_text  # Show what was transcribed
                    }))
                    
                    # Call Orchestrator
                    ai_text = await sync_to_async(self.orchestrator.get_ai_response)(user_text)
                    
                    # Read intent (same as text path)
                    intent = self.orchestrator.context.get('last_intent', None)
                    canvas_commands = self.orchestrator.context.get('last_canvas_commands', [])
                    teaching_script = self.orchestrator.context.get('last_teaching_script', [])
                    
                    # Build response — teacher intent gets teacher_response type
                    # so voice-supervisor.html opens the teaching canvas
                    voice_response = {
                        'message': ai_text,
                        'type': 'teacher_response' if intent == 'teacher' else 'ai_response'
                    }
                    if canvas_commands:
                        voice_response['canvas_commands'] = canvas_commands
                    if teaching_script:
                        voice_response['teaching_script'] = teaching_script
                    
                    await self.send(text_data=json.dumps(voice_response))
                    
                    # Canvas routing for voice — same as text path
                    if intent == 'teacher':
                        await self.send(text_data=json.dumps({
                            'type': 'route_to_view',
                            'view': 'canvas',
                            'intent': intent
                        }))
                        print(f"🔀 [Voice] Routing to canvas for teacher intent")
                    elif intent == 'coder':
                        await self.send(text_data=json.dumps({'type': 'route_to_view', 'view': 'editor', 'intent': intent}))
                    elif intent == 'examiner':
                        await self.send(text_data=json.dumps({'type': 'route_to_view', 'view': 'assessment', 'intent': intent}))
                    
                    # Generate Audio Response (TTS)
                    agent_type = self._determine_agent_type()
                    audio_bytes = await self.moss_tts.generate_audio(
                        text=ai_text,
                        agent=agent_type,
                        session_id=self.session_id
                    )
                    if audio_bytes:
                        await self.send(bytes_data=audio_bytes)
                else:
                    # Just send ACK if no speech detected
                    await self.send(text_data=json.dumps({
                        'type': 'audio_ack',
                        'message': 'received',
                        'emotion': emotion_label
                    }))
            except Exception as e:
                print(f"Audio Processing Error: {e}")
            return

        if text_data:
            print(f"📥 Received text message: {text_data[:200]}")  # Debug log
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')
            msg_type = text_data_json.get('type') 
            sub_type = text_data_json.get('event_type') 
            context_payload = text_data_json.get('context') or {}
            print(f"📊 Message type: {msg_type}, sub_type: {sub_type}, message: {message}")  # Debug log 

            # 1. Handle Chat Messages (Trigger AI)
            if msg_type == "context_update" and sub_type == "chat_message":
                self.orchestrator.context['canvas_mode'] = bool(context_payload.get('canvas_mode', False))

                # ── Socratic Mode: pass topic / mode / canvas_snapshot through ─
                ctx_topic = context_payload.get('topic')
                ctx_mode  = context_payload.get('mode')
                ctx_snap  = context_payload.get('canvas_snapshot')

                if ctx_topic:
                    self.orchestrator.context['current_topic_id'] = ctx_topic
                    self.orchestrator.context['topic'] = ctx_topic
                if ctx_mode:
                    self.orchestrator.context['mode'] = ctx_mode
                if ctx_snap:
                    self.orchestrator.context['canvas_snapshot'] = ctx_snap
                    logger.info(f"[Consumer] Canvas snapshot received ({len(ctx_snap)} chars)")
                else:
                    # Clear stale snapshot between messages
                    self.orchestrator.context.pop('canvas_snapshot', None)
                # ──────────────────────────────────────────────────────────────

                # Gap 5: Sending a message = user is active — reset idle clock
                self.last_activity_time = time.time()
                self.telemetry_monitor.record_mouse_event()  # Count as activity
                # Reset TTS cursor — new message, fresh utterance
                self.explanation_cursor = 0
                self._current_tts_text = ""
                # Call Orchestrator to get AI response (Wrapped in sync_to_async)
                ai_text = await sync_to_async(self.orchestrator.get_ai_response)(message)

                # ── v3: mode_transition event ────────────────────────────────
                new_render_mode = self.orchestrator.context.get('last_render_mode', 'default')
                tree_data       = self.orchestrator.context.get('last_tree_data')
                if new_render_mode != self.prev_render_mode:
                    await self.send(text_data=json.dumps({
                        'type':       'mode_transition',
                        'from':       self.prev_render_mode,
                        'to':         new_render_mode,
                        'tree_data':  tree_data,
                    }))
                    logger.info(f"[Consumer] mode_transition {self.prev_render_mode} → {new_render_mode}")
                    self.prev_render_mode = new_render_mode
                # ─────────────────────────────────────────────────────────────
                # ── v2: phase_change event ─────────────────────────────────────
                new_session_phase = self.orchestrator.context.get('last_session_phase', 'diagnostic')
                if new_session_phase != self.prev_session_phase:
                    await self.send(text_data=json.dumps({
                        'type':  'phase_change',
                        'from':  self.prev_session_phase,
                        'to':    new_session_phase,
                    }))
                    logger.info(f"[Consumer] phase_change {self.prev_session_phase} → {new_session_phase}")
                    self.prev_session_phase = new_session_phase

                # ── v2: answer detection for practice/adjustment phases ────────
                if new_session_phase in ('practice', 'adjustment', 'minitest'):
                    _ai_lower = ai_text.lower()
                    _correct_signals = ('correct', 'well done', 'exactly', 'great job', "that's right", 'perfect', 'you got it')
                    _wrong_signals   = ('not quite', 'incorrect', 'try again', 'actually', 'close but', "that's not", 'almost but')
                    _detected_correct = any(s in _ai_lower for s in _correct_signals)
                    _detected_wrong   = any(s in _ai_lower for s in _wrong_signals)
                    if _detected_correct:
                        await sync_to_async(self.orchestrator.record_answer)(True)
                    elif _detected_wrong:
                        await sync_to_async(self.orchestrator.record_answer)(False)
                # ─────────────────────────────────────────────────────────────────
                
                # Get the agent intent and canvas commands from orchestrator context
                intent = self.orchestrator.context.get('last_intent', None)
                canvas_commands = self.orchestrator.context.get('last_canvas_commands', [])
                teaching_script = self.orchestrator.context.get('last_teaching_script', [])
                
                # Send AI Response back to Frontend
                response_data = {
                    'message': ai_text,
                    'type': 'teacher_response' if intent == 'teacher' else 'ai_response',
                    'render_mode': new_render_mode,
                }
                
                # Generate Visual Commands (if applicable)
                # Only generate if teacher/visionary intent or if canvas_mode is active
                canvas_mode = self.orchestrator.context.get('canvas_mode', False)
                if (intent in ['teacher', 'visionary'] or canvas_mode) and not canvas_commands:
                    try:
                        # Generate canvas commands only if it makes sense
                        if should_generate_visual(message, ai_text):
                            from ai_engine.concept_extractor import extract_concept_for_visualization
                            
                            # Extract primary concept for visualization
                            rag_chunks = self.orchestrator.context.get('last_rag_chunks', [])
                            primary_concept = extract_concept_for_visualization(
                                rag_chunks=rag_chunks,
                                llm_response=ai_text,
                                query=message
                            )
                            
                            # Store for potential reuse
                            self.orchestrator.context['last_primary_concept'] = primary_concept
                            
                            # Generate canvas commands
                            visual_gen = VisualExplanationGenerator()
                            canvas_commands_objs = visual_gen.generate_for_concept(
                                primary_concept, message, context=ai_text
                            )
                            
                            # Convert to dictionaries using standardized function
                            canvas_commands = [
                                _convert_canvas_command_to_dict(cmd) 
                                for cmd in canvas_commands_objs
                            ]
                            
                            # Store in context for potential canvas_ready event
                            self.orchestrator.context['last_canvas_commands'] = canvas_commands
                            
                            logger.info(f"Generated {len(canvas_commands)} canvas commands for concept: {primary_concept}")
                    except Exception as e:
                        logger.error(f"Error generating visual commands: {e}", exc_info=True)

                # Include canvas commands if present
                if canvas_commands and len(canvas_commands) > 0:
                    response_data['canvas_commands'] = canvas_commands
                    print(f"🎨 Sending {len(canvas_commands)} canvas commands to frontend")

                if teaching_script and len(teaching_script) > 0:
                    response_data['teaching_script'] = teaching_script
                    print(f"📘 Sending teaching script with {len(teaching_script)} phases")
                
                await self.send(text_data=json.dumps(response_data))

                # Send page routing based on agent intent
                # 'general' and 'empath' stay in supervisor panel — no workspace opens
                WORKSPACE_INTENTS = {'teacher', 'coder', 'examiner', 'visionary'}
                if intent in WORKSPACE_INTENTS:
                    view_mapping = {
                        'teacher':   'canvas',
                        'coder':     'editor',
                        'examiner':  'assessment',
                        'visionary': 'dashboard',
                    }
                    target_view = view_mapping.get(intent)
                    if target_view:
                        await self.send(text_data=json.dumps({
                            'type': 'route_to_view',
                            'view': target_view,
                            'intent': intent
                        }))
                        print(f"🔀 Routing to {target_view} page based on {intent} intent")
                else:
                    print(f"💬 [{intent}] intent — staying in supervisor panel")

                # 2. Generate and Send Voice — streaming with barge-in + resume support
                agent_type = self._determine_agent_type()
                self.audio_stop_event.clear()    # Reset from any prior interrupt
                self._current_tts_text = ai_text # Store for potential resume
                self.explanation_cursor = 0      # Reset cursor for new utterance

                async def _stream_tts():
                    import re
                    _sentences = [
                        s for s in re.split(r'(?<=[.!?])\s+', ai_text.strip()) if s.strip()
                    ] or [ai_text]
                    _char_offset = 0
                    for _sentence in _sentences:
                        if self.audio_stop_event.is_set():
                            break
                        self.explanation_cursor = _char_offset  # mark start of this sentence
                        async for chunk in self.moss_tts.generate_audio_stream(
                            text=_sentence,
                            agent=agent_type,
                            session_id=self.session_id,
                            stop_event=self.audio_stop_event,
                        ):
                            await self.send(bytes_data=chunk)
                        _char_offset += len(_sentence) + 1
                    # Fully completed — reset cursor
                    if not self.audio_stop_event.is_set():
                        self.explanation_cursor = 0
                    logger.info(f"[TTS Stream] Done for session={self.session_id}")

                # Run as cancelable task so an 'interrupt' message can stop it
                self._tts_task = asyncio.ensure_future(_stream_tts())

            elif msg_type == "interrupt":
                # ── Barge-in: user spoke while agent was talking ─────────────
                self.audio_stop_event.set()   # signals streaming TTS to stop
                if self._tts_task and not self._tts_task.done():
                    self._tts_task.cancel()
                await self.send(text_data=json.dumps({
                    'type':   'audio_interrupted',
                    'cursor': self.explanation_cursor,
                }))
                logger.info(f"[Consumer] Barge-in at cursor={self.explanation_cursor} session={self.session_id}")

            elif msg_type == "resume_audio":
                # ── Resume TTS from cursor after barge-in ───────────────────────
                _resume_agent = self._determine_agent_type()
                _resume_cursor = self.explanation_cursor
                _resume_text = self._current_tts_text

                if not _resume_text or _resume_cursor >= len(_resume_text):
                    await self.send(text_data=json.dumps({
                        'type': 'audio_resume_skipped', 'reason': 'no_text'
                    }))
                else:
                    self.audio_stop_event.clear()

                    async def _resume_tts():
                        import re
                        _tail = _resume_text[_resume_cursor:].lstrip()
                        _sentences = [
                            s for s in re.split(r'(?<=[.!?])\s+', _tail.strip()) if s.strip()
                        ] or [_tail]
                        _char_offset = _resume_cursor
                        for _sentence in _sentences:
                            if self.audio_stop_event.is_set():
                                break
                            self.explanation_cursor = _char_offset
                            async for chunk in self.moss_tts.generate_audio_stream(
                                text=_sentence,
                                agent=_resume_agent,
                                session_id=self.session_id,
                                stop_event=self.audio_stop_event,
                            ):
                                await self.send(bytes_data=chunk)
                            _char_offset += len(_sentence) + 1
                        if not self.audio_stop_event.is_set():
                            self.explanation_cursor = 0
                        logger.info(f"[TTS Resume] Done for session={self.session_id}")

                    self._tts_task = asyncio.ensure_future(_resume_tts())
                    await self.send(text_data=json.dumps({
                        'type': 'audio_resumed', 'cursor': _resume_cursor
                    }))
                    logger.info(f"[Consumer] TTS resume from cursor={_resume_cursor}")

            elif msg_type == "canvas_ready":
                # Set canvas mode flag
                self.orchestrator.context['canvas_mode'] = True
                
                # Retrieve stored context
                query = self.orchestrator.context.get('last_teacher_query')
                response = self.orchestrator.context.get('last_teacher_response')
                teaching_script = self.orchestrator.context.get('last_teaching_script', [])
                canvas_commands = self.orchestrator.context.get('last_canvas_commands', [])
                primary_concept = self.orchestrator.context.get('last_primary_concept')

                # Fallback: Generate canvas commands if not already available
                if (not canvas_commands) and query and response and should_generate_visual(query, response):
                    try:
                        # Extract concept if not already stored
                        if not primary_concept:
                            from ai_engine.concept_extractor import extract_concept_for_visualization
                            rag_chunks = self.orchestrator.context.get('last_rag_chunks', [])
                            primary_concept = extract_concept_for_visualization(
                                rag_chunks=rag_chunks,
                                llm_response=response,
                                query=query
                            )
                            logger.info(f"Canvas ready fallback: extracted concept '{primary_concept}'")
                        
                        # Generate commands
                        generator = VisualExplanationGenerator()
                        canvas_commands_raw = generator.generate_for_concept(
                            primary_concept, query, context=response
                        )
                        
                        # Convert using standardized function
                        canvas_commands = [
                            _convert_canvas_command_to_dict(cmd)
                            for cmd in canvas_commands_raw
                        ]
                        
                        # Store in context
                        self.orchestrator.context['last_canvas_commands'] = canvas_commands
                        logger.info(f"Canvas ready: generated {len(canvas_commands)} commands")
                    except Exception as e:
                        logger.error(f"Error in canvas_ready fallback generation: {e}", exc_info=True)

                if canvas_commands:
                    response_data = {
                        'type': 'teacher_response',
                        'canvas_commands': canvas_commands
                    }
                    if teaching_script:
                        response_data['teaching_script'] = teaching_script
                    await self.send(text_data=json.dumps(response_data))

            # 2. Handle Code Changes
            elif msg_type == "context_update" and sub_type == "code_change":
                 await sync_to_async(self.orchestrator.update_context)('code_change', message)

            # 3. Handle Quiz Results (Feed to Analyst)
            elif msg_type == "quiz_result":
                # { "correct_count": 3, "total": 3, ... }
                # We need to pass this to the Swarm.
                # For now, we update context, or trigger a "Quiz Report" flow.
                # We'll treat it as a user message: "I got 3/3 on the quiz".
                
                user_report = f"I completed the quiz. Score: {text_data_json.get('correct_count')}/{text_data_json.get('total')}"
                
                # We also inject the raw result into the state if orchestrator supports it.
                # simpler approach: Just tell the AI so the Analyst sees it in the history.
                ai_text = await sync_to_async(self.orchestrator.get_ai_response)(user_report)
                
                await self.send(text_data=json.dumps({
                    'message': ai_text, # "Great job!"
                    'type': 'ai_response' 
                }))
                
                # TTS (MOSS)
                agent_type = self._determine_agent_type()
                audio_bytes = await self.moss_tts.generate_audio(
                    text=ai_text,
                    agent=agent_type,
                    session_id=self.session_id
                )
                if audio_bytes:
                    await self.send(bytes_data=audio_bytes)

            # 3. Handle Generic Broadcast
            elif msg_type == "vision_request":
                # { "image": "base64...", "event_type": "vision_request_auto" }
                image_data = text_data_json.get('image')
                
                # 1. Inject Image into Context (Orchestrator will prioritize it)
                self.orchestrator.context['current_image'] = image_data
                
                # 2. Trigger AI Response with implicit prompt
                # The Orchestrator will see 'current_image' and route to Visionary
                prompt = "I just drew something on the board. Can you check it?"
                
                ai_text = await sync_to_async(self.orchestrator.get_ai_response)(prompt)
                
                # 3. Send Response Back
                await self.send(text_data=json.dumps({
                    'message': ai_text,
                    'type': 'ai_response' 
                }))
                
                # 4. TTS (MOSS)
                agent_type = self._determine_agent_type()
                audio_bytes = await self.moss_tts.generate_audio(
                    text=ai_text,
                    agent=agent_type,
                    session_id=self.session_id
                )
                if audio_bytes:
                    await self.send(bytes_data=audio_bytes)
            
            # Gap 5: Handle telemetry events (mouse, keyboard)
            elif msg_type == "telemetry_event":
                event_type = text_data_json.get('event_type')
                
                # Update last activity time for pause detection
                self.last_activity_time = time.time()
                
                # Record telemetry events
                if event_type == "mouse_event":
                    self.telemetry_monitor.record_mouse_event()
                elif event_type == "keypress":
                    self.telemetry_monitor.record_keypress()
                elif event_type == "error":
                    error_type = text_data_json.get('error_type', 'unknown')
                    self.telemetry_monitor.record_error(error_type)
                elif event_type == "problem_completion":
                    success = text_data_json.get('success', False)
                    time_taken = text_data_json.get('time_taken', 0.0)
                    self.telemetry_monitor.record_problem_completion(success, time_taken)
                elif event_type == "topic_change":
                    new_topic = text_data_json.get('topic', '')
                    self.telemetry_monitor.update_topic(new_topic)
                elif event_type == "activity_change":
                    new_activity = text_data_json.get('activity_type', 'learning')
                    self.telemetry_monitor.set_activity_type(new_activity)

            # 3. Handle Generic Broadcast
            # else: pass (Removed to fix elif chain)
    
    def _determine_agent_type(self):
        """
        Determine which agent voice to use based on context/intent
        Returns: agent name (teacher, coder, examiner, visionary, empath)
        """
        # Check for explicit intent in orchestrator context
        intent = self.orchestrator.context.get('last_intent')
        
        # Map intents to agents
        intent_to_agent = {
            'quiz': 'examiner',
            'assessment': 'examiner',
            'test': 'examiner',
            'code': 'coder',
            'debug': 'coder',
            'program': 'coder',
            'algorithm': 'coder',
            'insight': 'visionary',
            'analytics': 'visionary',
            'progress': 'visionary',
            'struggle': 'empath',
            'difficulty': 'empath',
            'frustration': 'empath',
            'support': 'empath'
        }
        
        if intent:
            intent_lower = intent.lower()
            for keyword, agent in intent_to_agent.items():
                if keyword in intent_lower:
                    return agent
        
        # Check emotion state (if stressed/frustrated -> empath)
        emotion = self.orchestrator.context.get('current_emotion')
        if emotion in ['stress', 'anxiety', 'frustration', 'overwhelm']:
            return 'empath'
        
        # Check if canvas/drawing is active -> visionary
        if self.orchestrator.context.get('canvas_mode'):
            return 'visionary'
        
        # Default to teacher for general instruction
        return 'teacher'
    
    async def _stream_telemetry(self):
        """
        Gap 5: Background task to stream telemetry updates every 10 seconds
        Also detects pauses for canvas validation triggers
        """
        from ai_engine.gaps.visionary_heuristics import ImmediateHeuristicEngine
        
        heuristic_engine = ImmediateHeuristicEngine()
        pause_alert_sent = False
        
        try:
            while True:
                await asyncio.sleep(10)  # 10-second interval
                
                # Check if should capture snapshot
                if self.telemetry_monitor.should_capture_snapshot():
                    snapshot = self.telemetry_monitor.get_snapshot()
                    
                    # Skip if snapshot is None
                    if not snapshot:
                        continue
                    
                    # Run heuristic analysis
                    telemetry_dict = {
                        'idle_time': snapshot.idle_time,
                        'error_count': snapshot.error_count,
                        'velocity_score': snapshot.velocity_score,
                        'mouse_events': snapshot.mouse_events,
                        'keypress_count': snapshot.keypress_count,
                        'activity_type': snapshot.activity_type,
                        'current_topic': snapshot.current_topic
                    }
                    
                    alerts = heuristic_engine.analyze_telemetry(telemetry_dict)
                    
                    # Determine if user is in an active workspace (not just on supervisor page)
                    last_intent = self.orchestrator.context.get('last_intent', 'general')
                    in_workspace = last_intent in ('teacher', 'coder', 'examiner', 'visionary')

                    # Filter alerts: only send idle alerts when student is in a workspace
                    # On supervisor/general page, idle is expected — student may be reading
                    filtered_alerts = [
                        a for a in alerts
                        if not (a.alert_type == 'idle_spike' and not in_workspace)
                    ]

                    # Send telemetry update to frontend
                    await self.send(text_data=json.dumps({
                        'type': 'telemetry_update',
                        'metrics': {
                            'idle_time': snapshot.idle_time,
                            'error_count': snapshot.error_count,
                            'velocity_score': snapshot.velocity_score,
                            'mouse_events': snapshot.mouse_events,
                            'keypress_count': snapshot.keypress_count,
                            'activity_type': snapshot.activity_type,
                            'current_topic': snapshot.current_topic,
                            'timestamp': snapshot.timestamp.isoformat()
                        },
                        'alerts': [
                            {
                                'type': alert.alert_type,
                                'severity': alert.severity,
                                'message': alert.message,
                                'recommendation': alert.recommended_action
                            }
                            for alert in filtered_alerts
                        ] if filtered_alerts else []
                    }))
                
                # Gap 5: Detect pause (5+ seconds of inactivity)
                time_since_activity = time.time() - self.last_activity_time
                if time_since_activity >= 5.0 and not pause_alert_sent:
                    # Trigger canvas validation opportunity
                    await self.send(text_data=json.dumps({
                        'type': 'pause_detected',
                        'pause_duration': time_since_activity,
                        'message': 'Pause detected - canvas validation available'
                    }))
                    pause_alert_sent = True
                elif time_since_activity < 5.0:
                    # Reset pause flag when activity resumes
                    pause_alert_sent = False
        
        except asyncio.CancelledError:
            print(f"[Telemetry Stream] Stopped for session {self.session_id}")
        except Exception as e:
            print(f"[Telemetry Stream] Error: {e}")
            import traceback
            traceback.print_exc()
