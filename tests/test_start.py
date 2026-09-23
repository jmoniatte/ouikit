import io
import unittest
from unittest.mock import MagicMock, patch

from ouikit.start import start


class StartTest(unittest.TestCase):
    def test_refuses_to_start_without_a_terminal(self):
        make_app = MagicMock()
        with (
            patch("sys.stdin", io.StringIO()),
            patch("sys.stderr", new_callable=io.StringIO) as stderr,
            patch("ouikit.start.query_terminal") as query,
        ):
            with self.assertRaises(SystemExit) as raised:
                start("demo", make_app)
        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(stderr.getvalue(), "demo: needs a terminal on stdin and stdout\n")
        query.assert_not_called()
        make_app.assert_not_called()


if __name__ == "__main__":
    unittest.main()
