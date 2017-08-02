from os import path

from nio.util.versioning.dependency import DependsOn
from niocore.common.executable_request import ExecutableRequest
from niocore.core.component import CoreComponent
from nio import discoverable
from niocore.util.environment import NIOEnvironment

from .log_entries import LogEntries
from .executor import LogExecutor
from .core_handler import CoreLogHandler
from .service_handler import ServiceLogHandler


@DependsOn("niocore.components.rest", "0.1.0")
@discoverable
class LogManager(CoreComponent):

    """ Core component to handle logging functionality

    """

    _name = "LogManager"

    def __init__(self):
        """ Initializes the component

        """
        super().__init__()
        self._handlers = []
        # dependency components
        self._rest_manager = None
        self._service_manager = None

    def configure(self, context):
        """ Configures log manager

        Makes sure it gets a reference to its dependencies

        Args:
            context (CoreContext): component initialization context

        """

        super().configure(context)

        # Register dependencies to rest and service manager
        self._rest_manager = self.get_dependency('RESTManager')
        self._service_manager = self.get_dependency('ServiceManager')

    def start(self):
        """ Starts component

        Creates and registers web handlers

        """
        super().start()

        # create REST specific handlers
        self._handlers.append(CoreLogHandler("/log", self))
        self._handlers.append(ServiceLogHandler("/log/service", self))

        for handler in self._handlers:
            # Add handler to WebServer
            self._rest_manager.add_web_handler(handler)

    def stop(self):
        """ Stops component

        Removes web handlers

        """
        for handler in self._handlers:
            # Remove handler from WebServer
            self._rest_manager.remove_web_handler(handler)
        super().stop()

    @staticmethod
    def set_log_level(logger_name, level):
        """ Sets the log level at the core level

        Args:
            logger_name (str): Logger name
            level (LogLevel enum): Level to set
        """

        executor = LogExecutor()
        executor.set_log_level(logger_name, level)

    @staticmethod
    def get_logger_names(add_level):
        """ Gets the core level logger names

        Args:
            add_level (bool): Add level to list

        Returns:
            logger details - name and level - (list)

        """
        executor = LogExecutor()
        return executor.get_logger_names(add_level)

    def set_service_log_level(self, service_name, logger_name, level):
        """ Sets the log level to a service logger

        Args:
            service_name (str): Service name
            logger_name (str): Logger name, if empty, interpret as all
            level (LogLevel enum): Level to set

        Raises:
            RuntimeError: if service is not running
        """

        request = ExecutableRequest(LogExecutor,
                                    "set_log_level",
                                    logger_name,
                                    level)
        return self._service_manager.execute_request(service_name, request)

    def get_service_logger_names(self, service_name, add_level):
        """ Provides logger names for a service

        Args:
            service_name (str): Service name
            add_level (bool): Add level to list

        Returns:
            logger names (list)
            add_level (bool): Add level to list

        Raises:
            RuntimeError: if service is not running
        """

        request = ExecutableRequest(LogExecutor,
                                    "get_logger_names",
                                    add_level=add_level)
        return self._service_manager.execute_request(service_name, request)

    @staticmethod
    def get_log_entries(name, entries_count=-1, level=None, component=None):
        """ Retrieves log entries

        Allows to specify number of enties to read and
        filter by level and component

        Args:
            name (str): filename identifier (full filename is figured out by
                adding project path and extension
            entries_count (int): number of entries to read (-1 reads them all)
            level (str): level to filter by
            component (str): component to filter by

        Returns:
             list of entries where items are in dict format
        """
        filename = path.join(
            NIOEnvironment.get_path("logs"), "{}.log".format(name)
        )
        if not path.isfile(filename):
            raise ValueError("{} is not a valid log file".format(filename))
        return LogEntries.read(filename, entries_count, level, component)
