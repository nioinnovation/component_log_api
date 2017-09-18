from unittest.mock import patch

from nio.testing.test_case import NIOTestCase

from ..log_entries import LogEntries, LogEntry
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
                "[log time2] NIO [log level2] [log component2] log msg2",
                "[log time3] NIO [log level3] [log component3] log msg3"
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

            # verify levels argument
            result = manager.get_log_entries("filename", 2,
                                             levels=["log level2"])
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
            # assert that it fetches the two now since the levels allow for it
            result = manager.get_log_entries("filename", 2,
                                             levels=["log level1", "log level2"])
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

    def _get_entries_dict(self):
        return \
            {
                "file1": [
                    LogEntry({"time": 1}),
                    LogEntry({"time": 3}),
                    LogEntry({"time": 1000})
                ],
                "file2": [
                    LogEntry({"time": 1}),
                    LogEntry({"time": 2}),
                    LogEntry({"time": 6})
                ],
                "file3": [
                    LogEntry({"time": 100}),
                    LogEntry({"time": 200}),
                    LogEntry({"time": 600})
                ]
            }

    def _get_entries(self, filename, num_entries, level, component):
        return self._get_entries_dict()[filename]

    def test_read_all(self):
        """ Asserts read_all functionality and their resulting merge
        """
        with patch.object(LogEntries, "read",
                          side_effect=self._get_entries):
            # assert returning all sorted entries
            entries = LogEntries.read_all(list(self._get_entries_dict().keys()),
                                          None, None, None)
            self.assertEqual(len(entries), 9)
            for i in range(len(entries) - 1):
                self.assertLessEqual(entries[i]["time"],
                                     entries[i + 1]["time"])

            # assert returning last 3 sorted entries
            entries = LogEntries.read_all(list(self._get_entries_dict().keys()),
                                          3, None, None)
            self.assertEqual(len(entries), 3)
            expected_entries = [200, 600, 1000]
            for i in range(len(entries) - 1):
                # assert ordering
                self.assertLessEqual(entries[i]["time"],
                                     entries[i + 1]["time"])
                # assert values
                self.assertEqual(entries[i]["time"], expected_entries[i])
                self.assertEqual(entries[i+1]["time"], expected_entries[i+1])

    def test_merge(self):
        """ Asserts merge functionality
        """
        a = [LogEntry({"time": 1}), LogEntry({"time": 4}),
             LogEntry({"time": 7}), LogEntry({"time": 10})]
        b = [LogEntry({"time": 2}), LogEntry({"time": 5}),
             LogEntry({"time": 8}), LogEntry({"time": 11})]
        c = [LogEntry({"time": 3}), LogEntry({"time": 6}),
             LogEntry({"time": 9}), LogEntry({"time": 12})]

        merged_entries = LogEntries._merge_entries([a, b , c])
        # assert ordering
        for i in range(len(merged_entries) - 1):
            self.assertLessEqual(merged_entries[i]["time"],
                                 merged_entries[i+1]["time"])
        # assert values
        for i in range(len(merged_entries)):
            self.assertEqual(merged_entries[i]["time"], i+1)
