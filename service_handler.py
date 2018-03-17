import json
from nio.modules.security.access import ensure_access
from nio.util.logging import get_nio_logger
from nio.modules.web import RESTHandler


class ServiceLogHandler(RESTHandler):

    """ Handles service log requests
    """

    def __init__(self, route, log_manager):
        super().__init__(route)
        self._log_manager = log_manager
        self.logger = get_nio_logger("ServiceLogHandler")

    def on_get(self, request, response, *args, **kwargs):

        # Ensure instance "read" access in order to get service log levels
        ensure_access("instance", "read")

        params = request.get_params()
        self.logger.info("ServiceLogHandler.on_get, params: {0}".
                         format(params))

        if "identifier" not in params:
            raise RuntimeError("Service name not provided")

        service = params["identifier"]

        add_level = False
        if "level" in params:
            add_level = params['level'].upper() != 'FALSE'

        logger_names = \
            self._log_manager.get_service_logger_names(service,
                                                       add_level)

        # prepare response
        response.set_header('Content-Type', 'application/json')
        response.set_body(json.dumps(logger_names))

    def on_post(self, request, response, *args, **kwargs):

        # Ensure instance "write" access in order to modify service log levels
        ensure_access("instance", "write")

        params = request.get_params()
        body = request.get_body()
        self.logger.info("ServiceLogHandler.on_post, params: {0}, body: {1}".
                         format(params, body))
        if "identifier" not in params:
            raise RuntimeError("Service name not provided")

        # gather parameters
        service = params["identifier"]

        if "logger_name" in body:
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

        self._log_manager.set_service_log_level(service,
                                                logger_name,
                                                level)

    def on_put(self, request, response, *args, **kwargs):
        return self.on_post(request, response, args, kwargs)
