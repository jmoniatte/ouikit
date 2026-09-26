import threading
import time
import unittest

from tui_kit import processes


class ProcessesTest(unittest.TestCase):
    def test_run_passes_input_and_captures_output(self):
        result = processes.run(["cat"], timeout=5, input="hello")
        self.assertEqual((result.returncode, result.stdout), (0, "hello"))
        self.assertEqual(processes._running, set())

    def test_stop_all_ends_a_running_command_at_once(self):
        results = []
        worker = threading.Thread(target=lambda: results.append(processes.run(["sleep", "5"], timeout=10)))
        started = time.monotonic()
        worker.start()
        while not processes._running and time.monotonic() - started < 2:
            time.sleep(0.01)
        processes.stop_all()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertLess(time.monotonic() - started, 2)
        self.assertNotEqual(results[0].returncode, 0)


if __name__ == "__main__":
    unittest.main()
