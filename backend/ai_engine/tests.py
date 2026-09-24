from django.test import SimpleTestCase

from ai_engine.pbl.consumers import PBLConsumer
from ai_engine.pbl.consumers import _select_arch_mode
from ai_engine.pbl.live_contract import TURN_INTERRUPTED, TURN_LISTENING
from ai_engine.pbl.policy_guard import apply_socratic_policy
from ai_engine.pbl.pbl_graph import _normalize_progress_state, _summarize_canvas_state


class PBLGraphProgressStateTests(SimpleTestCase):
	def _base_state(self, **overrides):
		state = {
			'progress_state': None,
			'struggle_type': None,
			'current_code': '',
			'canvas_state': None,
			'time_since_last_action': 0.0,
			'attempt_count': 0,
		}
		state.update(overrides)
		return state

	def test_not_started_when_no_artifacts(self):
		state = self._base_state()
		self.assertEqual(_normalize_progress_state(state), 'not_started')

	def test_stuck_when_idle_threshold_crossed(self):
		state = self._base_state(time_since_last_action=35, attempt_count=1)
		self.assertEqual(_normalize_progress_state(state), 'stuck')

	def test_in_progress_when_control_flow_exists(self):
		state = self._base_state(current_code='for i in range(3):\n    pass')
		self.assertEqual(_normalize_progress_state(state), 'in_progress')

	def test_almost_done_when_return_exists_with_attempts(self):
		state = self._base_state(
			current_code='def solve(x):\n    return x',
			attempt_count=1,
		)
		self.assertEqual(_normalize_progress_state(state), 'almost_done')

	def test_started_when_canvas_has_content_only(self):
		state = self._base_state(canvas_state={'drawings': [{'type': 'line'}]})
		self.assertEqual(_normalize_progress_state(state), 'started')


class PBLCanvasSummaryTests(SimpleTestCase):
	def test_summary_for_blank_canvas(self):
		self.assertEqual(
			_summarize_canvas_state({'text_blocks': [], 'drawings': [], 'notes': []}),
			'Canvas present but currently blank.',
		)

	def test_summary_counts_artifacts(self):
		summary = _summarize_canvas_state({
			'text_blocks': ['a'],
			'drawings': [{'type': 'rect'}, {'type': 'line'}],
			'notes': ['n1'],
		})
		self.assertIn('text_blocks=1', summary)
		self.assertIn('drawings=2', summary)
		self.assertIn('notes=1', summary)


class PBLPolicyGuardTests(SimpleTestCase):
	def test_blocks_direct_solution_pattern(self):
		result = apply_socratic_policy('Here is the full answer. Copy and paste this code.')
		self.assertTrue(result.blocked)
		self.assertEqual(result.reason, 'direct_answer_pattern')
		self.assertIn('step by step', result.text.lower())

	def test_allows_guiding_question(self):
		result = apply_socratic_policy('Nice start. What value should this variable hold first?')
		self.assertFalse(result.blocked)
		self.assertIsNone(result.reason)


class PBLStaleTurnProtectionTests(SimpleTestCase):
	def _consumer(self):
		consumer = PBLConsumer()
		consumer._turn_state = TURN_LISTENING
		consumer._active_turn_id = 'session:voice:2'
		return consumer

	def test_marks_mismatched_turn_as_stale(self):
		consumer = self._consumer()
		self.assertTrue(consumer._is_stale_turn('session:voice:1'))

	def test_current_turn_is_not_stale(self):
		consumer = self._consumer()
		self.assertFalse(consumer._is_stale_turn('session:voice:2'))

	def test_interrupted_state_marks_any_turn_stale(self):
		consumer = self._consumer()
		consumer._turn_state = TURN_INTERRUPTED
		self.assertTrue(consumer._is_stale_turn('session:voice:2'))


class PBLCutoverModeSelectionTests(SimpleTestCase):
	def test_force_legacy_wins(self):
		mode = _select_arch_mode('abc', enabled=True, force_mode='legacy', canary_percent=100)
		self.assertEqual(mode, 'legacy')

	def test_force_new_wins(self):
		mode = _select_arch_mode('abc', enabled=True, force_mode='new', canary_percent=0)
		self.assertEqual(mode, 'new')

	def test_disabled_returns_legacy(self):
		mode = _select_arch_mode('abc', enabled=False, force_mode='auto', canary_percent=100)
		self.assertEqual(mode, 'legacy')

	def test_canary_zero_returns_legacy(self):
		mode = _select_arch_mode('abc', enabled=True, force_mode='auto', canary_percent=0)
		self.assertEqual(mode, 'legacy')

	def test_canary_full_returns_new(self):
		mode = _select_arch_mode('abc', enabled=True, force_mode='auto', canary_percent=100)
		self.assertEqual(mode, 'new')
