from unittest.mock import MagicMock, patch

from nio.testing.test_case import NIOTestCase

from ..log_entries import LogEntries, LogEntry
from ..manager import LogManager


class TestLogManagerEntries(NIOTestCase):

    def _patch_service_list(self, manager, services=[]):
        service_manager = MagicMock()
        service_manager.instances.configuration.get_children.return_value = \
            services
        manager._service_manager = service_manager

    def test_log_entries_invalid_service_name(self):
        """ Assert an invalid service name is caught
        """
        manager = LogManager()
        self._patch_service_list(manager)
        with self.assertRaises(ValueError):
            manager.get_log_entries("servicename", 2)

    @patch(LogManager.__module__ + ".path")
    def test_log_entries_invalid_file(self, path):
        """ Assert an invalid file with a valid service name returns no logs
        """
        manager = LogManager()
        self._patch_service_list(manager, "servicename")
        result = manager.get_log_entries("servicename", 2)
        self.assertEqual(result, [])

    @patch(LogManager.__module__ + ".path")
    def test_log_entries(self, _):
        """ Assert parsing and filtering
        """
        manager = LogManager()
        self._patch_service_list(manager, ["filename"])
        with patch.object(LogEntries, "_get_file_contents") as mock_contents:
            mock_contents.return_value = []
            result = manager.get_log_entries("filename", 2)
            self.assertEqual(len(result), 0)

            mock_contents.return_value = \
                ["[log time] NIO [DEBUG] [log component] log msg"]
            result = manager.get_log_entries("filename", 2)
            self.assertEqual(len(result), 1)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time",
                    "level": "DEBUG",
                    "component": "log component",
                    "msg": "log msg"
                }
            )

            mock_contents.return_value = [
                "[log time1] NIO [INFO] [log component1] log msg1",
                "[log time2] NIO [DEBUG] [log component2] log msg2"
            ]

            # verify count argument
            result = manager.get_log_entries("filename", 1)
            self.assertEqual(len(result), 1)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time1",
                    "level": "INFO",
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
                    "level": "DEBUG",
                    "component": "log component2",
                    "msg": "log msg2"
                }
            )
            self.assertDictEqual(
                result[1],
                {
                    "time": "log time1",
                    "level": "INFO",
                    "component": "log component1",
                    "msg": "log msg1"
                }
            )

            # verify level argument
            result = manager.get_log_entries("filename", 2,
                                             level="INFO")
            self.assertEqual(len(result), 1)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time1",
                    "level": "INFO",
                    "component": "log component1",
                    "msg": "log msg1"
                }
            )
            # setting DEBUG as lowest level allowed, retrieves all
            result = manager.get_log_entries("filename", 2,
                                             level="DEBUG")
            # both entries were allowed since desired level is DEBUG and above
            self.assertEqual(len(result), 2)

            result = manager.get_log_entries("filename", 2,
                                             level="ERROR")
            # no entries with level ERROR and above
            self.assertEqual(len(result), 0)

            # verify component argument
            result = manager.get_log_entries("filename", 2,
                                             component="log component1")
            self.assertEqual(len(result), 1)
            self.assertDictEqual(
                result[0],
                {
                    "time": "log time1",
                    "level": "INFO",
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
