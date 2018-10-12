import heapq
from collections import deque
import logging
from datetime import datetime

from nio.util.logging import get_nio_logger


class LogEntry(dict):
    """ Provides comparison operators to the dictionary elements
    """
    def __eq__(self, other):
        return self["time"] == other["time"]

    def __ne__(self, other):
        return not (self["time"] == other["time"])

    def __lt__(self, other):
        return self["time"] < other["time"]


class _LogEntries(object):
    def __init__(self):
        self.logger = get_nio_logger("LogEntries")

    def read(self, filename, num_entries, level, component):
        """ Read entries from a nio log file

        Args:
            filename (str): path to file with log entries
            num_entries (int): number of entries to read, if -1 read all
            level (str): filter entries with this level if not None
            component (str): filter entries with this component if not None

        Returns:
             list of entries where items are in dict format
        """
        self.logger.debug("Reading {} log file".format(filename))

        entries_read = 0
        entries = deque()
        if level:
            level = logging._nameToLevel[level]
        else:
            # when no level is specified, assume lowest level and above desired,
            # thus allowing all entries based on level
            level = logging.DEBUG

        extended = []
        for row in self._get_file_contents(filename):
            entry = self._parse_row(row)
            if entry is None:
                continue
            # time == None if not first row of message
            if entry["time"] is not None:
                if entry["level"] is not None:
                    if not self._is_level_allowed(
                            level, logging._nameToLevel[entry["level"]]):
                        continue
                else:
                    continue
                # filter by component?
                if component and entry["component"] != component:
                    continue
                # any extended rows buffered belong under this first row
                entry["msg"] += "".join(reversed(extended))
                extended = []
                entries_read += 1
                entries.appendleft(entry)
                # number of entries specified?
                if num_entries != -1 and entries_read == num_entries:
                    break
            else:
                # rows are being read bottom to top, so extended rows are
                # buffered here until another first row is read
                extended.append(row)
        return list(entries)

    def read_all(self, files, num_entries, level, component):
        """ Reads and merge log entries from given files

        When merging, this method takes advantage of the fact that
        incoming lists are already sorted.

        Args:
            files (list): list of absolute path to files
            num_entries (int): number of entries to read, if -1 read all
            level (str): filter entries with this level if not None
            component (str): filter entries with this component if not None

        Returns:
             list of entries where items are in dict format
        """
        entries_read = []
        for filename in files:
            try:
                entries_read.append(
                    LogEntries.read(filename, num_entries, level, component)
                )
            except IOError:
                self.logger.error("Failed to read {} log file".format(filename))

        # merge entries
        result = self._merge_entries(entries_read)
        return result[-num_entries:] if num_entries else result

    def _parse_row(self, row):
        continued = False
        closing_bracket1 = row.find("]")
        if closing_bracket1 == -1:
            # line does not conform to expected format
            # likely to be an exception row
            self.logger.debug("Row: {} is invalid".format(row))
            continued = True
            time = None
        else:
            time = row[1:closing_bracket1]
            # validate time
            try:
                datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                try:
                    # Additional check for timestamps using old nio_time format 
                    datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    self.logger.debug("Invalid time: {} in row: {}".format(time, row))
                    time = None

        closing_bracket2 = row.find("]", closing_bracket1 + 1)
        if closing_bracket2 == -1:
            # line does not conform ro expected format
            # likely to be an exception row
            self.logger.debug("Row: {} is invalid".format(row))
            continued = True
            level = None
        else:
            level = row[closing_bracket1 + 7: closing_bracket2]
            # validate level
            if level not in logging._nameToLevel:
                self.logger.debug("Invalid level: {} in row: {}".format(level, row))
                level = None

        closing_bracket3 = row.find("]", closing_bracket2 + 1)
        if closing_bracket3 == -1:
            # line does not conform ro expected format
            # likely to be an exception row
            self.logger.debug("Row: {} is invalid".format(row))
            continued = True
            component_name = None
        else:
            component_name = row[closing_bracket2 + 3: closing_bracket3]
            self.logger.debug("OK: {}".format(row))
            msg = row[closing_bracket3 + 2:]
        if continued:
            msg = row

        return \
            LogEntry({
                "time": time,
                "level": level,
                "component": component_name,
                "msg": msg
            })

    @staticmethod
    def _get_file_contents(filename):
        with open(filename, "r") as f:
            return reversed(f.readlines())

    @staticmethod
    def _is_level_allowed(level, entry_level):
        return entry_level >= level

    @staticmethod
    def _merge_entries(lists):
        return [item for item in heapq.merge(*lists)]

LogEntries = _LogEntries()
