import json
from unittest.mock import MagicMock
from nio.modules.web.http import Request
from nio.testing.modules.security.module import TestingSecurityModule

from ..core_handler import CoreLogHandler
from niocore.testing.web_test_case import NIOCoreWebTestCase


class TestCoreLogHandler(NIOCoreWebTestCase):

    def get_module(self, module_name):
        # Don't want to test permissions, use the test module
        if module_name == 'security':
            return TestingSecurityModule()
        else:
            return super().get_module(module_name)

    def test_on_get(self):
        manager = MagicMock()
        loggers = [{"name": "a logger"}]
        manager.get_logger_names.return_value = loggers
        handler = CoreLogHandler("", manager)
        # Request without 'level' param
        mock_req = MagicMock(spec=Request)
        mock_req.get_params.return_value = {}
        request = mock_req
        response = MagicMock()
        handler.on_get(request, response)
        response_body = response.set_body.call_args[0][0]
        self.assertEqual(response_body, json.dumps(loggers))
        manager.get_logger_names.assert_called_with(False)
        # Request with 'level' param
        mock_req = MagicMock(spec=Request)
        mock_req.get_params.return_value = {"level": "true"}
        request = mock_req
        response = MagicMock()
        handler.on_get(request, response)
        response_body = response.set_body.call_args[0][0]
        self.assertEqual(response_body, json.dumps(loggers))
        manager.get_logger_names.assert_called_with(True)

        # log entries requests
        mock_req = MagicMock(spec=Request)

        # assert defaults
        mock_req.get_params.return_value = {"identifier": "entries"}
        manager.get_log_entries = MagicMock()
        manager.get_log_entries.return_value = []
        request = mock_req
        handler.on_get(request, response)
        manager.get_log_entries.assert_called_with(None, 100, None, None)
        manager.get_log_entries.reset_mock()

        # assert query parameters are passed along
        mock_req.get_params.return_value = {"identifier": "entries",
                                            "name": "service1",
                                            "count": 20,
                                            "levels": "ERROR",
                                            "component": "component_name"}
        handler.on_get(request, response)
        manager.get_log_entries.assert_called_with("service1", 20,
                                                   ["ERROR"], "component_name")

    def test_on_post(self):
        manager = MagicMock()
        mock_req = MagicMock(spec=Request)
        mock_req.get_body.return_value = {"log_level": "ERROR"}
        mock_req.get_params.return_value = {"identifier": "logger"}
        handler = CoreLogHandler("", manager)
        request = mock_req
        response = MagicMock()
        handler.on_post(request, response)
        manager.set_log_level.assert_called_with('logger', 'ERROR')
