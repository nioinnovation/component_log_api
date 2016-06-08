import logging


class LogExecutor(object):

    """ Proxy executing log functionality such as obtain logger names and
    changing log level """

    @staticmethod
    def get_logger_names(add_level=False):
        """ Retrieves log names  withing current process

        Args:
            add_level (bool): Add level to list

        Returns:
            logger details - name and level - (list)

        """
        if add_level:
            return [
                {"name": key,
                 "level": logging.getLevelName(
                     logging.getLogger(key).getEffectiveLevel())}
                for key in logging.getLogger().manager.loggerDict.keys()
                ]

        return [{"name": key}
                for key in logging.getLogger().manager.loggerDict.keys()]

    @staticmethod
    def set_log_level(logger_name, level):
        """ Sets the log level to a logger withing current process

        Args:
            logger_name (str): Logger name
            level (LogLevel enum): Level to set

        """
        if logger_name:
            if logger_name in logging.getLogger().manager.loggerDict.keys():
                logging.getLogger(logger_name).setLevel(level)
            else:
                raise RuntimeError("Logger: {0} does not exists".
                                   format(logger_name))
        else:
            # if no logger_name specified, set it to all
            for key in logging.getLogger().manager.loggerDict.keys():
                logging.getLogger(key).setLevel(level)
