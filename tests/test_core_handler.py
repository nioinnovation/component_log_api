import json
import threading
from unittest.mock import Mock
from nio.modules.security.user import User
from nio.modules.web.http import Request

from ..core_handler import CoreLogHandler

from niocore.testing.test_case import NIOCoreTestCase


class TestCoreLogHandler(NIOCoreTestCase):

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
        manager.get_logger_names = Mock(return_value=loggers)
        handler = CoreLogHandler("", manager)
        # Request without 'level' param
        request = Request(None, {}, None)
        response = Mock()
        handler.on_get(request, response)
        response_body = response.set_body.call_args[0][0]
        self.assertEqual(response_body, json.dumps(loggers))
        manager.get_logger_names.assert_called_with(False)
        # Request with 'level' param
        request = Request(None, {"level": "true"}, None)
        response = Mock()
        handler.on_get(request, response)
        response_body = response.set_body.call_args[0][0]
        self.assertEqual(response_body, json.dumps(loggers))
        manager.get_logger_names.assert_called_with(True)

    def test_on_post(self):
        manager = Mock()
        handler = CoreLogHandler("", manager)
        body = {"log_level": "ERROR"}
        params = {"identifier": "logger"}
        request = Request(body, params, None)
        response = Mock()
        handler.on_post(request, response)
        manager.set_log_level.assert_called_with('logger', 'ERROR')
