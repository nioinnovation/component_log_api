import json
import threading
from unittest.mock import Mock
from nio.modules.security.user import User
from nio.modules.web.http import Request
from niocore.testing.test_case import NIOCoreTestCase

from ..service_handler import ServiceLogHandler


class TestServiceLogHandler(NIOCoreTestCase):

    def get_test_modules(self):
        return super().get_test_modules() | {'security'}

    def setUp(self):
        super().setUp()
        setattr(threading.current_thread(), "user", User("tester"))

    def tearDown(self):
        delattr(threading.current_thread(), "user")
        super().tearDown()

    def test_on_get(self):
        manager = Mock()
        loggers = [{"name": "a logger"}]
        manager.get_service_logger_names = Mock(return_value=loggers)
        handler = ServiceLogHandler("", manager)
        # Request without 'level' param
        request = Request(None, {"identifier": "logger"}, None)
        response = Mock()
        handler.on_get(request, response)
        response_body = response.set_body.call_args[0][0]
        self.assertEqual(response_body, json.dumps(loggers))
        manager.get_service_logger_names.assert_called_with('logger', False)
        # Request with 'level' param
        request = Request(
            None, {"identifier": "logger", "level": "true"}, None)
        response = Mock()
        handler.on_get(request, response)
        response_body = response.set_body.call_args[0][0]
        self.assertEqual(response_body, json.dumps(loggers))
        manager.get_service_logger_names.assert_called_with('logger', True)

    def test_on_post(self):
        manager = Mock()
        handler = ServiceLogHandler("", manager)
        body = {"log_level": "ERROR",
                "logger_name": "logger"}
        params = {"identifier": "service"}
        request = Request(body, params, None)
        response = Mock()
        handler.on_post(request, response)
        manager.set_service_log_level.assert_called_with(
            'service', 'logger', 'ERROR')

    def test_on_put(self):
        manager = Mock()
        handler = ServiceLogHandler("", manager)
        body = {"log_level": "ERROR",
                "logger_name": "logger"}
        params = {"identifier": "service"}
        request = Request(body, params, None)
        response = Mock()
        handler.on_put(request, response)
        manager.set_service_log_level.assert_called_with(
            'service', 'logger', 'ERROR')
