import json
from nio.modules.security.access import ensure_access
from nio.util.logging import get_nio_logger
from nio.modules.web import RESTHandler


class CoreLogHandler(RESTHandler):

    """ Handles core log requests
    """

    def __init__(self, route, log_manager):
        super().__init__(route)
        self._log_manager = log_manager
        self.logger = get_nio_logger("CoreLogHandler")

    def on_get(self, request, response, *args, **kwargs):
        """ API endpoint to retrieve log information

        To retrieve log names use:
            http://[host]:[port]/log
        To retrieve log names and levels use:
            http://[host]:[port]/log?level

        To retrieve log entries use:
            - reads last 100 entries from main (core process)
                http://[host]:[port]/log/entries
            - reads last 100 entries at ERROR level from main
                http://[host]:[port]/log/entries?name=main&level=ERROR
            - reads last 20 entries at ERROR level from main
                http://[host]:[port]/log/entries?name=main&level=ERROR&count=20
            - reads last 100 entries at WARNING level for service 'service1'
                http://[host]:[port]/log/entries?name=service1&level=WARNING
            - reads last 100 entries for component 'main.BlockManager'
                http://[host]:[port]/log/entries?component=main.BlockManager

        """

        # Ensure instance "read" access in order to retrieve log levels
        ensure_access("instance", "read")

        self.logger.info("CoreLogHandler.on_get")
        params = request.get_params()

        # What route?
        if "identifier" in params and params["identifier"] == "entries":
            name = params.get("name", None)
            count = int(params.get("count", 100))
            level = params.get("level", None)
            component = params.get("component", None)
            result = self._log_manager.get_log_entries(
                name, count, level, component
            )
        else:
            add_level = False
            if "level" in params:
                add_level = params['level'].upper() != 'FALSE'
            result = self._log_manager.get_logger_names(add_level)

        response.set_header('Content-Type', 'application/json')
        response.set_body(json.dumps(result))

    def on_post(self, request, response, *args, **kwargs):

        # Ensure instance "write" access in order to change log levels
        ensure_access("instance", "write")

        params = request.get_params()
        body = request.get_body()
        self.logger.info("CoreLogHandler.on_post, params: {0}, body: {1}".
                         format(params, body))
        # grab logger name from parameters and if not then from body
        if "identifier" in params:
            logger_name = params["identifier"]
        elif "logger_name" in body:
            logger_name = body["logger_name"]
        else:
            # allow and/or set an empty logger_name since it is interpreted
            # as a request for all loggers.
            logger_name = ""

        level = body["log_level"]
        if not level:
            msg = "Level is invalid"
            self.logger.error(msg)
            raise RuntimeError(msg)

        self._log_manager.set_log_level(logger_name, level)

    def on_put(self, request, response, *args, **kwargs):
        return self.on_post(request, response, args, kwargs)
