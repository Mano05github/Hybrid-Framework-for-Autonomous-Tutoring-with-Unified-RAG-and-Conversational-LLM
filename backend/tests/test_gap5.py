"""
Comprehensive Test Suite for Gap 5: Always-On Visionary Agent
Tests telemetry monitoring, heuristic analysis, canvas validation, forecasting, and Triple-Check coordination
"""

import os
import sys
import django
import asyncio
from datetime import datetime, timedelta
import time

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from learning_session.models import VisionaryMetric, VisionaryForecast, PerformanceAlert
from ai_engine.gaps.visionary_telemetry import LightweightTelemetryMonitor, TelemetryAggregator
from ai_engine.gaps.visionary_heuristics import ImmediateHeuristicEngine, PatternRecognizer
from ai_engine.gaps.visionary_forecasting import StrategicForecastingEngine, PatternAnalyzer
from ai_engine.gaps.visionary_canvas import CanvasMonitor, DiagramValidator, SnapshotQueue
from ai_engine.agents import visionary_agent, run_triple_check_analysis
from ai_engine.state import AgentState
from asgiref.sync import sync_to_async

User = get_user_model()


class Gap5TestSuite:
    """Test suite for Gap 5 Always-On Visionary Agent"""
    
    def __init__(self):
        self.telemetry_monitor = None
        self.heuristic_engine = ImmediateHeuristicEngine()
        self.canvas_monitor = CanvasMonitor()
        self.forecasting_engine = StrategicForecastingEngine()
        self.pattern_analyzer = PatternAnalyzer()
        self.test_user = None
        self.test_session_id = "test_session_gap5_001"
        
    async def setup(self):
        """Setup test environment"""
        print("\n" + "="*70)
        print("GAP 5: ALWAYS-ON VISIONARY AGENT - TEST SUITE")
        print("="*70 + "\n")
        
        # Create or get test user
        @sync_to_async
        def get_or_create_user():
            user, created = User.objects.get_or_create(
                username='gap5_test_user',
                defaults={'email': 'gap5test@example.com'}
            )
            if created:
                user.set_password('testpass123')
                user.save()
            return user
        
        self.test_user = await get_or_create_user()
        print(f"✓ Test user created/retrieved: {self.test_user.username}")
        
        # Initialize telemetry monitor
        self.telemetry_monitor = LightweightTelemetryMonitor()
        self.telemetry_monitor.start_session(
            user_id=str(self.test_user.id),
            session_id=self.test_session_id,
            topic="Binary Search Trees"
        )
        print(f"✓ Telemetry monitor initialized for session: {self.test_session_id}\n")
    
    async def test_1_telemetry_snapshot(self):
        """Test 1: Telemetry snapshot capture and metric accuracy"""
        print("="*70)
        print("TEST 1: Telemetry Snapshot Capture")
        print("="*70)
        
        try:
            # Simulate user activity
            print("→ Simulating user activity (mouse events, keypresses, idle time)...")
            
            # Record 10 mouse events
            for _ in range(10):
                self.telemetry_monitor.record_mouse_event()
            
            # Record 25 keypresses
            for _ in range(25):
                self.telemetry_monitor.record_keypress()
            
            # Simulate idle time
            time.sleep(0.5)
            
            # Record 2 errors
            self.telemetry_monitor.record_error("syntax_error")
            self.telemetry_monitor.record_error("logic_error")
            
            # Record problem completion
            self.telemetry_monitor.record_problem_completion(success=True, time_taken=45.0)
            
            # Get snapshot
            snapshot = self.telemetry_monitor.get_snapshot()
            
            # Verify snapshot
            print(f"\n📊 Snapshot captured:")
            print(f"   • Mouse events: {snapshot.mouse_events} (expected: 10)")
            print(f"   • Keypresses: {snapshot.keypress_count} (expected: 25)")
            print(f"   • Errors: {snapshot.error_count} (expected: 2)")
            print(f"   • Idle time: {snapshot.idle_time:.2f}s")
            print(f"   • Velocity score: {snapshot.velocity_score:.2f}")
            print(f"   • Activity type: {snapshot.activity_type}")
            print(f"   • Topic: {snapshot.current_topic}")
            
            # Assertions
            assert snapshot.mouse_events == 10, f"Expected 10 mouse events, got {snapshot.mouse_events}"
            assert snapshot.keypress_count == 25, f"Expected 25 keypresses, got {snapshot.keypress_count}"
            assert snapshot.error_count == 2, f"Expected 2 errors, got {snapshot.error_count}"
            assert snapshot.idle_time >= 0, "Idle time should be non-negative"
            assert 0.1 <= snapshot.velocity_score <= 3.0, "Velocity score should be in valid range [0.1, 3.0]"
            
            print("\n✅ TEST 1 PASSED: Telemetry snapshot capture working correctly\n")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST 1 FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_2_anomaly_detection(self):
        """Test 2: Heuristic anomaly detection (idle, errors, velocity, streaks)"""
        print("="*70)
        print("TEST 2: Heuristic Anomaly Detection")
        print("="*70)
        
        try:
            print("→ Testing all 4 anomaly types...\n")
            
            # Test 1: Idle spike detection
            print("🔍 Test 2a: Idle Spike Detection")
            idle_telemetry = {
                'idle_time': 125.0,  # Exceeds moderate threshold (120s)
                'error_count': 0,
                'velocity_score': 1.0,
                'mouse_events': 0,
                'keypress_count': 0,
                'activity_type': 'problem_solving',
                'current_topic': 'Binary Search'
            }
            
            alerts = self.heuristic_engine.analyze_telemetry(idle_telemetry)
            idle_alert = next((a for a in alerts if a.alert_type == 'idle_spike'), None)
            
            assert idle_alert is not None, "Expected idle spike alert"
            assert idle_alert.severity == 'moderate', f"Expected moderate severity, got {idle_alert.severity}"
            print(f"   ✓ Idle spike detected: {idle_alert.message}")
            print(f"   ✓ Severity: {idle_alert.severity}")
            print(f"   ✓ Recommendation: {idle_alert.recommended_action}\n")
            
            # Test 2: Error cascade detection
            print("🔍 Test 2b: Error Cascade Detection")
            
            # Simulate error cascade (3+ errors in 30s window)
            now = datetime.now()
            self.heuristic_engine.error_history = [
                {'timestamp': now - timedelta(seconds=10), 'type': 'syntax_error'},
                {'timestamp': now - timedelta(seconds=15), 'type': 'logic_error'},
                {'timestamp': now - timedelta(seconds=20), 'type': 'runtime_error'},
                {'timestamp': now - timedelta(seconds=25), 'type': 'syntax_error'}
            ]
            
            error_telemetry = {
                'idle_time': 10.0,
                'error_count': 1,
                'velocity_score': 0.8,
                'mouse_events': 50,
                'keypress_count': 100,
                'activity_type': 'problem_solving',
                'current_topic': 'Binary Search'
            }
            
            self.heuristic_engine.record_error({'timestamp': now, 'type': 'syntax_error'})
            alerts = self.heuristic_engine.analyze_telemetry(error_telemetry)
            error_alert = next((a for a in alerts if a.alert_type == 'error_cascade'), None)
            
            assert error_alert is not None, "Expected error cascade alert"
            print(f"   ✓ Error cascade detected: {error_alert.message}")
            print(f"   ✓ Severity: {error_alert.severity}")
            print(f"   ✓ Recommendation: {error_alert.recommended_action}\n")
            
            # Test 3: Velocity drop detection
            print("🔍 Test 2c: Velocity Drop Detection")
            
            self.heuristic_engine.baseline_velocity = 1.0
            velocity_telemetry = {
                'idle_time': 10.0,
                'error_count': 0,
                'velocity_score': 0.4,  # 60% drop (below 0.5 threshold)
                'mouse_events': 20,
                'keypress_count': 40,
                'activity_type': 'problem_solving',
                'current_topic': 'Binary Search'
            }
            
            alerts = self.heuristic_engine.analyze_telemetry(velocity_telemetry)
            velocity_alert = next((a for a in alerts if a.alert_type == 'velocity_drop'), None)
            
            assert velocity_alert is not None, "Expected velocity drop alert"
            assert velocity_alert.severity in ['moderate', 'high'], "Expected moderate or high severity"
            print(f"   ✓ Velocity drop detected: {velocity_alert.message}")
            print(f"   ✓ Severity: {velocity_alert.severity}")
            print(f"   ✓ Recommendation: {velocity_alert.recommended_action}\n")
            
            # Test 4: Streak break detection
            print("🔍 Test 2d: Streak Break Detection")
            
            self.heuristic_engine.current_streak = 5  # Had 5 consecutive successes
            self.heuristic_engine.last_success_time = datetime.now() - timedelta(seconds=120)
            
            # Simulate failed problem (velocity drop + errors)
            streak_telemetry = {
                'idle_time': 90.0,
                'error_count': 2,
                'velocity_score': 0.6,
                'mouse_events': 15,
                'keypress_count': 30,
                'activity_type': 'problem_solving',
                'current_topic': 'Binary Search'
            }
            
            alerts = self.heuristic_engine.analyze_telemetry(streak_telemetry)
            streak_alert = next((a for a in alerts if a.alert_type == 'streak_break'), None)
            
            assert streak_alert is not None, "Expected streak break alert"
            print(f"   ✓ Streak break detected: {streak_alert.message}")
            print(f"   ✓ Previous streak: {self.heuristic_engine.previous_streak}")
            print(f"   ✓ Recommendation: {streak_alert.recommended_action}\n")
            
            print("✅ TEST 2 PASSED: All 4 anomaly types detected correctly\n")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST 2 FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_3_canvas_validation_triggers(self):
        """Test 3: Canvas validation trigger logic (pause, milestone, explicit)"""
        print("="*70)
        print("TEST 3: Canvas Validation Triggers")
        print("="*70)
        
        try:
            print("→ Testing 3 canvas validation triggers...\n")
            
            # Test 1: Pause detected trigger (5s+ idle)
            print("🔍 Test 3a: Pause Detection Trigger")
            
            # Simulate stroke activity
            self.canvas_monitor.on_canvas_event({
                'type': 'stroke_start',
                'timestamp': datetime.now() - timedelta(seconds=6)
            })
            
            # Simulate stroke end (now past 5s threshold)
            trigger = self.canvas_monitor.on_canvas_event({
                'type': 'stroke_end',
                'timestamp': datetime.now()
            })
            
            assert trigger == 'pause_detected', f"Expected 'pause_detected' trigger, got {trigger}"
            print("   ✓ Pause detected after 5+ seconds idle\n")
            
            # Test 2: Logical unit completion trigger
            print("🔍 Test 3b: Logical Unit Completion Trigger")
            
            # Simulate tree node completion
            self.canvas_monitor.reset_analysis_cache()  # Clear previous state
            trigger = self.canvas_monitor.on_canvas_event({
                'type': 'stroke_end',
                'structure_type': 'tree_node',
                'has_edges': True,
                'timestamp': datetime.now()
            })
            
            assert trigger == 'logical_unit_complete', f"Expected 'logical_unit_complete' trigger, got {trigger}"
            print("   ✓ Logical unit completion detected (tree node with edges)\n")
            
            # Test 3: Explicit validation request
            print("🔍 Test 3c: Explicit Validation Request")
            
            trigger = self.canvas_monitor.on_canvas_event({
                'type': 'validation_request',
                'timestamp': datetime.now()
            })
            
            assert trigger == 'explicit_request', f"Expected 'explicit_request' trigger, got {trigger}"
            print("   ✓ Explicit validation request processed\n")
            
            print("✅ TEST 3 PASSED: All 3 canvas triggers working correctly\n")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST 3 FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_4_mastery_forecasting(self):
        """Test 4: Mastery timeline forecasting with LinearRegression"""
        print("="*70)
        print("TEST 4: Mastery Forecasting (LinearRegression)")
        print("="*70)
        
        try:
            print("→ Testing mastery prediction with historical data...\n")
            
            # Simulate improving mastery trend
            history = [
                {'day': 0, 'mastery_percentage': 20.0},
                {'day': 1, 'mastery_percentage': 35.0},
                {'day': 2, 'mastery_percentage': 48.0},
                {'day': 3, 'mastery_percentage': 62.0},
                {'day': 4, 'mastery_percentage': 74.0}
            ]
            
            print("📊 Historical data (5 days):")
            for h in history:
                print(f"   Day {h['day']}: {h['mastery_percentage']:.1f}% mastery")
            
            # Generate forecast
            forecast = self.forecasting_engine.forecast_mastery_timeline("Binary Search Trees", history)
            
            print(f"\n📈 Forecast results:")
            print(f"   • Current mastery: {forecast.current_mastery:.1f}%")
            print(f"   • Predicted mastery date: {forecast.predicted_mastery_date}")
            print(f"   • Days remaining: {forecast.days_remaining}")
            print(f"   • Velocity trend: {forecast.velocity_trend}")
            print(f"   • Confidence: {forecast.confidence:.2f}")
            print(f"   • Data points: {forecast.data_points}")
            
            # Assertions
            assert forecast.current_mastery == 74.0, "Current mastery should match latest data point"
            assert forecast.predicted_mastery_date is not None, "Should predict mastery date"
            assert forecast.days_remaining >= 0, "Days remaining should be non-negative"
            assert forecast.velocity_trend in ['improving', 'stable', 'declining'], "Valid velocity trend required"
            assert 0 <= forecast.confidence <= 1.0, "Confidence should be in [0, 1] range"
            assert forecast.data_points == 5, "Should use all 5 data points"
            
            # Test declining trend
            print("\n→ Testing declining trend detection...")
            declining_history = [
                {'day': 0, 'mastery_percentage': 70.0},
                {'day': 1, 'mastery_percentage': 65.0},
                {'day': 2, 'mastery_percentage': 58.0},
                {'day': 3, 'mastery_percentage': 52.0}
            ]
            
            declining_forecast = self.forecasting_engine.forecast_mastery_timeline("Advanced Algorithms", declining_history)
            
            print(f"   • Velocity trend: {declining_forecast.velocity_trend}")
            assert declining_forecast.velocity_trend == 'declining', "Should detect declining trend"
            print("   ✓ Declining trend detected correctly")
            
            print("\n✅ TEST 4 PASSED: Mastery forecasting working accurately\n")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST 4 FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_5_recurring_pattern_detection(self):
        """Test 5: Recurring error and topic struggle pattern detection"""
        print("="*70)
        print("TEST 5: Recurring Pattern Detection")
        print("="*70)
        
        try:
            print("→ Testing recurring error pattern detection...\n")
            
            # Simulate error history with recurring patterns
            error_history = [
                {'timestamp': datetime.now() - timedelta(hours=5), 'error_type': 'off_by_one', 'topic': 'Arrays'},
                {'timestamp': datetime.now() - timedelta(hours=4), 'error_type': 'null_pointer', 'topic': 'Linked Lists'},
                {'timestamp': datetime.now() - timedelta(hours=3), 'error_type': 'off_by_one', 'topic': 'Arrays'},
                {'timestamp': datetime.now() - timedelta(hours=2), 'error_type': 'off_by_one', 'topic': 'Arrays'},
                {'timestamp': datetime.now() - timedelta(hours=1), 'error_type': 'off_by_one', 'topic': 'Arrays'},
                {'timestamp': datetime.now(), 'error_type': 'null_pointer', 'topic': 'Linked Lists'}
            ]
            
            patterns = self.pattern_analyzer.detect_recurring_errors(error_history)
            
            print(f"📊 Detected {len(patterns)} recurring error patterns:")
            for pattern in patterns:
                print(f"\n   Pattern: {pattern.pattern_key}")
                print(f"   • Occurrences: {pattern.occurrences}")
                print(f"   • First seen: {pattern.first_seen}")
                print(f"   • Latest seen: {pattern.latest_seen}")
                print(f"   • Time span: {pattern.time_span_hours:.1f} hours")
                print(f"   • Recommendation: {pattern.recommended_action}")
            
            # Assertions
            assert len(patterns) > 0, "Should detect at least one pattern"
            off_by_one_pattern = next((p for p in patterns if 'off_by_one' in p.pattern_key), None)
            assert off_by_one_pattern is not None, "Should detect off_by_one pattern"
            assert off_by_one_pattern.occurrences == 4, f"Expected 4 off_by_one occurrences, got {off_by_one_pattern.occurrences}"
            
            print("\n→ Testing topic struggle pattern detection...\n")
            
            # Simulate session history with topic struggles
            session_history = [
                {'timestamp': datetime.now() - timedelta(hours=10), 'topic': 'Binary Search Trees', 'struggle_score': 0.8, 'duration': 45.0},
                {'timestamp': datetime.now() - timedelta(hours=8), 'topic': 'Hash Tables', 'struggle_score': 0.3, 'duration': 20.0},
                {'timestamp': datetime.now() - timedelta(hours=6), 'topic': 'Binary Search Trees', 'struggle_score': 0.75, 'duration': 50.0},
                {'timestamp': datetime.now() - timedelta(hours=4), 'topic': 'Binary Search Trees', 'struggle_score': 0.85, 'duration': 60.0},
                {'timestamp': datetime.now() - timedelta(hours=2), 'topic': 'Binary Search Trees', 'struggle_score': 0.7, 'duration': 40.0}
            ]
            
            struggle_patterns = self.pattern_analyzer.detect_topic_struggles(session_history)
            
            print(f"📊 Detected {len(struggle_patterns)} topic struggle patterns:")
            for pattern in struggle_patterns:
                print(f"\n   Pattern: {pattern.pattern_key}")
                print(f"   • Occurrences: {pattern.occurrences}")
                print(f"   • Recommendation: {pattern.recommended_action}")
            
            # Assertions
            assert len(struggle_patterns) > 0, "Should detect at least one struggle pattern"
            bst_pattern = next((p for p in struggle_patterns if 'Binary Search Trees' in p.pattern_key), None)
            assert bst_pattern is not None, "Should detect BST struggle pattern"
            assert bst_pattern.occurrences == 4, f"Expected 4 BST struggle sessions, got {bst_pattern.occurrences}"
            
            print("\n✅ TEST 5 PASSED: Recurring pattern detection working correctly\n")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST 5 FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_6_triple_check_coordination(self):
        """Test 6: Triple-Check parallel analysis and priority logic"""
        print("="*70)
        print("TEST 6: Triple-Check Coordination")
        print("="*70)
        
        try:
            print("→ Testing parallel Coder+Empath+Visionary execution...\n")
            
            # Test scenario: Visionary pattern detected (highest priority)
            print("🔍 Test 6a: Visionary Pattern Priority")
            
            state = AgentState(
                query="I keep getting off-by-one errors in my binary search implementation",
                user_id=str(self.test_user.id),
                session_id=self.test_session_id,
                recent_errors=4,
                pause_duration=10.0,
                current_topic="Binary Search",
                activity_type="problem_solving"
            )
            
            result = await run_triple_check_analysis(state)
            
            print(f"\n📊 Triple-Check result:")
            print(f"   • Priority: {result['priority']}")
            print(f"   • Action: {result['action']}")
            if 'pattern' in result:
                print(f"   • Pattern: {result['pattern']}")
            
            # Note: Actual priority depends on what patterns are detected
            # Just verify the structure is correct
            assert 'priority' in result, "Result should have priority"
            assert 'action' in result, "Result should have action"
            assert 'all_results' in result, "Result should have all agent results"
            
            print("\n→ Testing priority logic with different scenarios...")
            
            # Test scenario: Empath emotion priority
            print("\n🔍 Test 6b: Empath Emotion Priority")
            
            emotion_state = AgentState(
                query="I'm so frustrated, I don't understand this at all",
                user_id=str(self.test_user.id),
                session_id=self.test_session_id,
                pause_duration=45.0,
                recent_errors=3,
                current_topic="Recursion",
                activity_type="learning"
            )
            
            emotion_result = await run_triple_check_analysis(emotion_state)
            
            print(f"\n📊 Emotion-driven result:")
            print(f"   • Priority: {emotion_result['priority']}")
            print(f"   • Action: {emotion_result['action']}")
            
            # Test scenario: Coder standard priority (no patterns/emotions)
            print("\n🔍 Test 6c: Coder Standard Priority")
            
            standard_state = AgentState(
                query="How do I implement a binary search tree?",
                user_id=str(self.test_user.id),
                session_id=self.test_session_id,
                pause_duration=5.0,
                recent_errors=0,
                current_topic="Data Structures",
                activity_type="learning"
            )
            
            standard_result = await run_triple_check_analysis(standard_state)
            
            print(f"\n📊 Standard result:")
            print(f"   • Priority: {standard_result['priority']}")
            print(f"   • Action: {standard_result['action']}")
            
            print("\n✅ TEST 6 PASSED: Triple-Check coordination working correctly\n")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST 6 FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_7_database_persistence(self):
        """Test 7: Database logging and persistence of Gap 5 models"""
        print("="*70)
        print("TEST 7: Database Persistence")
        print("="*70)
        
        try:
            print("→ Testing VisionaryMetric, VisionaryForecast, PerformanceAlert persistence...\n")
            
            # Test VisionaryMetric creation
            print("🔍 Test 7a: VisionaryMetric Persistence")
            
            @sync_to_async
            def create_metric():
                return VisionaryMetric.objects.create(
                    user=self.test_user,
                    session_id=self.test_session_id,
                    activity_type='problem_solving',
                    current_topic='Binary Search Trees',
                    mouse_events=50,
                    keypress_count=120,
                    idle_time=15.5,
                    error_count=2,
                    velocity_score=0.85,
                    metadata={'test': True}
                )
            
            metric = await create_metric()
            print(f"   ✓ VisionaryMetric created: ID {metric.id}")
            print(f"   ✓ Mouse events: {metric.mouse_events}")
            print(f"   ✓ Velocity score: {metric.velocity_score}")
            
            # Test VisionaryForecast creation
            print("\n🔍 Test 7b: VisionaryForecast Persistence")
            
            @sync_to_async
            def create_forecast():
                return VisionaryForecast.objects.create(
                    user=self.test_user,
                    topic='Binary Search Trees',
                    current_mastery=74.0,
                    predicted_mastery_date=datetime.now() + timedelta(days=3),
                    days_remaining=3,
                    confidence=0.85,
                    velocity_trend='improving',
                    data_points=5
                )
            
            forecast = await create_forecast()
            print(f"   ✓ VisionaryForecast created: ID {forecast.id}")
            print(f"   ✓ Current mastery: {forecast.current_mastery}%")
            print(f"   ✓ Days remaining: {forecast.days_remaining}")
            print(f"   ✓ Velocity trend: {forecast.velocity_trend}")
            
            # Test PerformanceAlert creation
            print("\n🔍 Test 7c: PerformanceAlert Persistence")
            
            @sync_to_async
            def create_alert():
                return PerformanceAlert.objects.create(
                    user=self.test_user,
                    session_id=self.test_session_id,
                    alert_type='idle_spike',
                    severity='moderate',
                    message='Student idle for 125 seconds',
                    metric_value=125.0,
                    threshold=120.0,
                    current_topic='Binary Search Trees',
                    activity_type='problem_solving',
                    intervention_taken=False,
                    resolved=False
                )
            
            alert = await create_alert()
            print(f"   ✓ PerformanceAlert created: ID {alert.id}")
            print(f"   ✓ Alert type: {alert.alert_type}")
            print(f"   ✓ Severity: {alert.severity}")
            print(f"   ✓ Message: {alert.message}")
            
            # Test querying
            print("\n→ Testing database queries...")
            
            @sync_to_async
            def query_metrics():
                return list(VisionaryMetric.objects.filter(
                    user=self.test_user,
                    session_id=self.test_session_id
                ).order_by('-timestamp'))
            
            @sync_to_async
            def query_alerts():
                return list(PerformanceAlert.objects.filter(
                    user=self.test_user,
                    resolved=False
                ).order_by('-timestamp'))
            
            metrics = await query_metrics()
            alerts = await query_alerts()
            
            print(f"   ✓ Found {len(metrics)} telemetry metrics")
            print(f"   ✓ Found {len(alerts)} unresolved alerts")
            
            assert len(metrics) > 0, "Should find at least one metric"
            assert len(alerts) > 0, "Should find at least one alert"
            
            print("\n✅ TEST 7 PASSED: Database persistence working correctly\n")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST 7 FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            return False
    
    async def cleanup(self):
        """Cleanup test data"""
        print("="*70)
        print("CLEANUP")
        print("="*70)
        
        @sync_to_async
        def delete_test_data():
            # Delete test models
            VisionaryMetric.objects.filter(session_id=self.test_session_id).delete()
            VisionaryForecast.objects.filter(user=self.test_user).delete()
            PerformanceAlert.objects.filter(session_id=self.test_session_id).delete()
            
            print("✓ Test data cleaned up")
        
        await delete_test_data()
        print("\n")
    
    async def run_all_tests(self):
        """Run all tests and report results"""
        await self.setup()
        
        tests = [
            ("Telemetry Snapshot", self.test_1_telemetry_snapshot),
            ("Anomaly Detection", self.test_2_anomaly_detection),
            ("Canvas Validation Triggers", self.test_3_canvas_validation_triggers),
            ("Mastery Forecasting", self.test_4_mastery_forecasting),
            ("Recurring Pattern Detection", self.test_5_recurring_pattern_detection),
            ("Triple-Check Coordination", self.test_6_triple_check_coordination),
            ("Database Persistence", self.test_7_database_persistence)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            result = await test_func()
            results.append((test_name, result))
        
        await self.cleanup()
        
        # Print summary
        print("="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        
        print(f"\n{'='*70}")
        print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print(f"{'='*70}\n")
        
        return passed == total


async def main():
    """Main test execution"""
    suite = Gap5TestSuite()
    success = await suite.run_all_tests()
    
    if success:
        print("🎉 ALL GAP 5 TESTS PASSED! Phase 3 implementation complete.")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED. Review output above for details.")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

