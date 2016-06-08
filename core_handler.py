import json
from nio.modules.security.decorator import protected_access
from nio.util.logging import get_nio_logger
from nio.modules.web import RESTHandler


class CoreLogHandler(RESTHandler):

    """ Handles core log requests
    """

    def __init__(self, route, log_manager):
        super().__init__(route)
        self._log_manager = log_manager
        self.logger = get_nio_logger("CoreLogHandler")

    @protected_access("logging.view")
    def on_get(self, request, response, *args, **kwargs):
        self.logger.info("CoreLogHandler.on_get")
        params = request.get_params()

        add_level = False
        if "level" in params:
            add_level = params['level'].upper() != 'FALSE'
        logger_names = self._log_manager.get_logger_names(add_level)

        response.set_header('Content-Type', 'application/json')
        response.set_body(json.dumps(logger_names))

    @protected_access("logging.modify")
    def on_post(self, request, response, *args, **kwargs):
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

    @protected_access("logging.modify")
    def on_put(self, request, response, *args, **kwargs):
        return self.on_post(request, response, args, kwargs)
