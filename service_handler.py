import json
from nio.modules.security.decorator import protected_access
from nio.util.logging import get_nio_logger
from nio.modules.web import RESTHandler


class ServiceLogHandler(RESTHandler):

    """ Handles service log requests
    """

    def __init__(self, route, log_manager):
        super().__init__(route)
        self._log_manager = log_manager
        self.logger = get_nio_logger("ServiceLogHandler")

    @protected_access("logging.view")
    def on_get(self, request, response, *args, **kwargs):
        params = request.get_params()
        self.logger.info("ServiceLogHandler.on_get, params: {0}".
                          format(params))

        if "identifier" not in params:
            raise RuntimeError("Service name not provided")

        service_name = params["identifier"]
        self._verify_service_name(service_name)

        add_level = False
        if "level" in params:
            add_level = params['level'].upper() != 'FALSE'

        logger_names = \
            self._log_manager.get_service_logger_names(service_name,
                                                       add_level)

        # prepare response
        response.set_header('Content-Type', 'application/json')
        response.set_body(json.dumps(logger_names))

    @protected_access("logging.modify")
    def on_post(self, request, response, *args, **kwargs):
        params = request.get_params()
        body = request.get_body()
        self.logger.info("ServiceLogHandler.on_post, params: {0}, body: {1}".
                          format(params, body))
        if "identifier" not in params:
            raise RuntimeError("Service name not provided")

        # gather parameters
        service_name = params["identifier"]

        if "logger_name" in body:
            logger_name = body["logger_name"]
        else:
            # allow and/or set an empty logger_name since it is interpreted
            # as a request for all loggers.
            logger_name = ""

        level = body["log_level"]

        # verify parameters
        self._verify_service_name(service_name)

        if not level:
            msg = "Level is invalid"
            self.logger.error(msg)
            raise RuntimeError(msg)

        self._log_manager.set_service_log_level(service_name,
                                                logger_name,
                                                level)

    @protected_access("logging.modify")
    def on_put(self, request, response, *args, **kwargs):
        return self.on_post(request, response, args, kwargs)

    def _verify_service_name(self, service_name):
        """ Makes sure service name is not empty

        Args:
            service_name (str): Service name

        """

        if not service_name:
            msg = "Service name is invalid"
            self.logger.error(msg)
            raise RuntimeError(msg)
