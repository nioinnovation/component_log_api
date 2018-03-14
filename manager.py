from os import path, listdir

from nio.util.versioning.dependency import DependsOn
from niocore.common.executable_request import ExecutableRequest
from niocore.core.api.resource import MultipleChoices
from niocore.core.component import CoreComponent
from nio import discoverable
from niocore.util.environment import NIOEnvironment

from .log_entries import LogEntries
from .executor import LogExecutor
from .core_handler import CoreLogHandler
from .service_handler import ServiceLogHandler
from . import __version__ as component_version


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

    def get_version(self):
        return component_version

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

    def set_service_log_level(self, service, logger_name, level):
        """ Sets the log level to a service logger

        Args:
            service (str): Service name or identifier
            logger_name (str): Logger name, if empty, interpret as all
            level (LogLevel enum): Level to set

        Raises:
            RuntimeError: if service is not running
        """

        service_id = self._identify_service(service)
        request = ExecutableRequest(LogExecutor,
                                    "set_log_level",
                                    logger_name,
                                    level)
        return self._service_manager.execute_request(service_id, request)

    def get_service_logger_names(self, service, add_level):
        """ Provides logger names for a service

        Args:
            service (str): Service name or identifier
            add_level (bool): Add level to list

        Returns:
            logger names (list)
            add_level (bool): Add level to list

        Raises:
            RuntimeError: if service is not running
        """

        service_id = self._identify_service(service)
        request = ExecutableRequest(LogExecutor,
                                    "get_logger_names",
                                    add_level=add_level)
        return self._service_manager.execute_request(service_id, request)

    def _service_list(self):
        return self._service_manager.instances.configuration.get_children()

    def get_log_entries(
            self, name, id=None, entries_count=-1, level=None, component=None):
        """ Retrieves log entries

        Allows to specify number of enties to read and
        filter by level and component

        Args:
            name (str): filename identifier (full filename is figured out by
                adding project path and extension), if name is None, all
                files in project's logs directory are considered
            id (str): service identifier
            entries_count (int): number of entries to read (-1 reads them all)
            level (str): level to filter by
            component (str): component to filter by

        Returns:
             list of entries where items are in dict format
        """
        if name or id:
            services = self._service_manager.services
            if id is not None and name is None:
                # figure out name from id
                name = services.get(id, None)
                if name is None:
                    raise ValueError("Invalid service id specified")
            else:
                if name != 'main' and name not in services.values():
                    raise ValueError("'{}' service does not exist".format(name))
            filename = path.join(
                NIOEnvironment.get_path("logs"), "{}.log".format(name)
            )
            if not path.isfile(filename):
                return []
            return LogEntries.read(filename, entries_count, level, component)
        else:
            # find all log project files
            files = []
            logs_dir = NIOEnvironment.get_path("logs")
            for filename in listdir(logs_dir):
                extension = path.splitext(filename)[1]
                if extension == ".log":
                    files.append(path.join(logs_dir, filename))

            return LogEntries.read_all(files, entries_count, level, component)

    def _identify_service(self, service):
        """ Identifies a service

        Args:
            service (str): Service name or id

        Returns:
             service id

        Raises:
            MultipleChoices if service name cannot be uniquely identified
            ValueError if service is invalid
        """
        services = self._service_manager.services
        if service in services:
            return service
        found = [id for id, name in services.items() if name == service]
        # handle multiple choices
        found_count = len(found)
        if found_count == 1:
            return found[0]
        elif found_count > 1:
            raise MultipleChoices(found)
        raise ValueError("Service: '{}' is invalid".format(service))

