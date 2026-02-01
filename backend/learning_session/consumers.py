import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .orchestrator import SessionOrchestrator
from .tts_service import TTSService
import asyncio
import time

# Store active orchestrators in memory (Simple dict for now, use Redis in Prod)
active_sessions = {}

# Store telemetry monitors for active sessions (Gap 5)
telemetry_monitors = {}

class LearningSessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'session_{self.session_id}'
        self.telemetry_task = None  # Gap 5: Background telemetry streaming task
        self.last_activity_time = time.time()  # Gap 5: Track for pause detection

        # Initialize Orchestrator for this session if not exists
        if self.session_id not in active_sessions:
            active_sessions[self.session_id] = SessionOrchestrator(self.session_id)
        
        self.orchestrator = active_sessions[self.session_id]
        self.tts_service = TTSService()
        
        # Gap 5: Initialize telemetry monitor
        from ai_engine.gaps.visionary_telemetry import LightweightTelemetryMonitor
        if self.session_id not in telemetry_monitors:
            telemetry_monitors[self.session_id] = LightweightTelemetryMonitor()
            # Start session tracking (user_id would come from auth context)
            user = self.scope.get('user')
            user_id = user.id if user and hasattr(user, 'id') else 'anonymous'
            telemetry_monitors[self.session_id].start_session(user_id, self.session_id)
        
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
                # 1. Use Google Cloud STT directly (no temp file needed)
                from ai_engine.stt import get_stt_engine
                from google.cloud import speech
                
                # 2. Analyze Emotion (Async)
                # Save to temp file only for emotion analysis
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                    temp_audio.write(bytes_data)
                    temp_path = temp_audio.name
                
                emotion_label = await sync_to_async(self.orchestrator.analyze_emotion)(temp_path)
                
                # 3. Transcribe Audio with Google Cloud STT
                stt_engine = get_stt_engine()
                user_text = await sync_to_async(stt_engine.transcribe_audio)(
                    audio_content=bytes_data,
                    language_code="en-US",
                    sample_rate=16000,
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16
                )

                # 4. Cleanup temp file
                os.remove(temp_path)
                
                # 5. Process Conversation (if text found)
                if user_text:
                    print(f"User said: {user_text}")
                    # Call Orchestrator
                    ai_text = await sync_to_async(self.orchestrator.get_ai_response)(user_text)
                    
                    # Send Text Response
                    await self.send(text_data=json.dumps({
                        'message': ai_text,
                        'type': 'ai_response' 
                    }))
                    
                    # Generate Audio Response (TTS)
                    audio_bytes = await self.tts_service.generate_audio(ai_text)
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
            print(f"📊 Message type: {msg_type}, sub_type: {sub_type}, message: {message}")  # Debug log 

            # 1. Handle Chat Messages (Trigger AI)
            if msg_type == "context_update" and sub_type == "chat_message":
                # Call Orchestrator to get AI response (Wrapped in sync_to_async)
                ai_text = await sync_to_async(self.orchestrator.get_ai_response)(message)
                
                # Get the agent intent and canvas commands from orchestrator context
                intent = self.orchestrator.context.get('last_intent', None)
                canvas_commands = self.orchestrator.context.get('last_canvas_commands', [])
                
                # Send AI Response back to Frontend
                response_data = {
                    'message': ai_text,
                    'type': 'teacher_response' if intent == 'teacher' else 'ai_response'
                }
                
                # Include canvas commands if present
                if canvas_commands and len(canvas_commands) > 0:
                    response_data['canvas_commands'] = canvas_commands
                    print(f"🎨 Sending {len(canvas_commands)} canvas commands to frontend")
                
                await self.send(text_data=json.dumps(response_data))

                # Send page routing based on agent intent
                if intent:
                    view_mapping = {
                        'teacher': 'canvas',
                        'coder': 'editor',
                        'examiner': 'assessment',
                        'visionary': 'dashboard',
                        'empath': 'voice'
                    }
                    
                    target_view = view_mapping.get(intent)
                    if target_view and target_view != 'voice':  # Don't redirect from voice page
                        await self.send(text_data=json.dumps({
                            'type': 'route_to_view',
                            'view': target_view,
                            'intent': intent
                        }))
                        print(f"🔀 Routing to {target_view} page based on {intent} intent")

                # 2. Generate and Send Voice (TTS)
                audio_bytes = await self.tts_service.generate_audio(ai_text)
                if audio_bytes:
                    await self.send(bytes_data=audio_bytes)

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
                
                # TTS
                audio_bytes = await self.tts_service.generate_audio(ai_text)
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
                
                # 4. TTS
                audio_bytes = await self.tts_service.generate_audio(ai_text)
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
                            for alert in alerts
                        ] if alerts else []
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
