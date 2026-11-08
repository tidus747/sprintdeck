import errno
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from sprintdeck.__main__ import main


class CLITests(unittest.TestCase):
    def test_default_port_fallback_and_printed_urls(self):
        with tempfile.TemporaryDirectory() as folder:
            server = Mock()
            server.server_port = 9001
            server.serve_forever.side_effect = KeyboardInterrupt
            with patch('sys.argv', ['sprintdeck', '--data', str(Path(folder) / 'session.json')]), \
                 patch('sprintdeck.__main__.Server', side_effect=[OSError(errno.EADDRINUSE, 'occupied'), server]) as factory, \
                 patch('builtins.print') as output:
                self.assertEqual(main(), 0)
                self.assertEqual(factory.call_args_list[0].args[0], ('127.0.0.1', 8765))
                self.assertEqual(factory.call_args_list[1].args[0], ('127.0.0.1', 0))
                self.assertTrue(any('http://127.0.0.1:9001/control' in str(call) for call in output.call_args_list))
                server.server_close.assert_called_once()

    def test_explicit_port_failure_does_not_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('sys.argv', ['sprintdeck', '--port', '9000', '--data', str(Path(folder) / 'session.json')]), \
                 patch('sprintdeck.__main__.Server', side_effect=OSError(errno.EADDRINUSE, 'occupied')) as factory, \
                 patch('builtins.print'):
                self.assertEqual(main(), 1)
                self.assertEqual(factory.call_count, 1)
