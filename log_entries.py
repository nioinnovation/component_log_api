from collections import deque


class _LogEntries(object):

    def read(self, filename, num_entries, level, component):
        """ Read entries from a nio log file

        Args:
            filename (str): path to file with log entries
            num_entries (int): number of entries to read, if -1 read all
            level (str): filter entries with this level if not None
            component (str): filter entries with this component if not None
        """
        entries_read = 0
        entries = deque()

        for row in self._get_file_contents(filename):
            entry = self._parse_row(row)
            if entry:
                # filter by level?
                if level and entry["level"] != level:
                    continue
                # filter by component?
                if component and entry["component"] != component:
                    continue
                entries_read += 1
                entries.appendleft(entry)
                # number of entries specified?
                if num_entries != -1 and entries_read == num_entries:
                    break
        return list(entries)

    @staticmethod
    def _get_file_contents(filename):
        with open(filename, "r") as f:
            return reversed(f.readlines())

    @staticmethod
    def _parse_row(row):
        closing_bracket1 = row.find(']')
        if closing_bracket1 == -1:
            # line does not conform ro expected format
            # likely to be an exception row
            return None
        time = row[1:closing_bracket1]

        closing_bracket2 = row.find(']', closing_bracket1 + 1)
        if closing_bracket2 == -1:
            # line does not conform ro expected format
            # likely to be an exception row
            return None
        level = row[closing_bracket1 + 7: closing_bracket2]

        closing_bracket3 = row.find(']', closing_bracket2 + 1)
        if closing_bracket3 == -1:
            # line does not conform ro expected format
            # likely to be an exception row
            return None
        component_name = row[closing_bracket2 + 3: closing_bracket3]

        msg = row[closing_bracket3 + 2:]

        return \
            {
                "time": time,
                "level": level,
                "component": component_name,
                "msg": msg
            }


LogEntries = _LogEntries()
