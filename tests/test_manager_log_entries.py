from unittest.mock import patch

from nio.testing.test_case import NIOTestCase

from ..log_entries import LogEntries
from ..manager import LogManager


class TestLogManagerEntries(NIOTestCase):

    def test_log_entries_invalid_file(self):
        """ Assert an invalid file is caught
        """
        manager = LogManager()
        with patch.object(LogEntries, "_get_file_contents") as mock_contents:
            mock_contents.return_value = []
            with self.assertRaises(ValueError):
                manager.get_log_entries("filename", 2)

    @patch(LogManager.__module__ + ".path")
    def test_log_entries(self, _):
        """ Assert parsing and filtering
        """
        manager = LogManager()
        with patch.object(LogEntries, "_get_file_contents") as mock_contents:
            mock_contents.return_value = []
            result = manager.get_log_entries("filename", 2)
            self.assertEqual(len(result), 0)

            mock_contents.return_value = \
                ["[log time] NIO [log level] [log component] log msg"]
            result = manager.get_log_entries("filename", 2)
            self.assertEqual(len(result), 1)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time",
                    "level": "log level",
                    "component": "log component",
                    "msg": "log msg"
                }
            )

            mock_contents.return_value = [
                "[log time1] NIO [log level1] [log component1] log msg1",
                "[log time2] NIO [log level2] [log component2] log msg2"
            ]

            # verify count argument
            result = manager.get_log_entries("filename", 1)
            self.assertEqual(len(result), 1)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time1",
                    "level": "log level1",
                    "component": "log component1",
                    "msg": "log msg1"
                }
            )

            result = manager.get_log_entries("filename", 2)
            self.assertEqual(len(result), 2)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time2",
                    "level": "log level2",
                    "component": "log component2",
                    "msg": "log msg2"
                }
            )
            self.assertDictEqual(
                result[1],
                {
                    "time": "log time1",
                    "level": "log level1",
                    "component": "log component1",
                    "msg": "log msg1"
                }
            )

            # verify level argument
            result = manager.get_log_entries("filename", 2,
                                             level="log level2")
            self.assertEqual(len(result), 1)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time2",
                    "level": "log level2",
                    "component": "log component2",
                    "msg": "log msg2"
                }
            )

            # verify component argument
            result = manager.get_log_entries("filename", 2,
                                             component="log component1")
            self.assertEqual(len(result), 1)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time1",
                    "level": "log level1",
                    "component": "log component1",
                    "msg": "log msg1"
                }
            )
