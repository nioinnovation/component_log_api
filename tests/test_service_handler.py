import json
from unittest.mock import MagicMock
from nio.modules.web.http import Request
from nio.testing.modules.security.module import TestingSecurityModule

from ..service_handler import ServiceLogHandler
from niocore.testing.web_test_case import NIOCoreWebTestCase


class TestServiceLogHandler(NIOCoreWebTestCase):

    def get_module(self, module_name):
        # Don't want to test permissions, use the test module
        if module_name == 'security':
            return TestingSecurityModule()
        else:
            return super().get_module(module_name)

    def test_on_get(self):
        manager = MagicMock()
        loggers = [{"name": "a logger"}]
        manager.get_service_logger_names.return_value = loggers
        handler = ServiceLogHandler("", manager)
        # Request without 'level' param
        mock_req = MagicMock(spec=Request)
        mock_req.get_params.return_value = {"identifier": "logger"}
        response = MagicMock()
        handler.on_get(mock_req, response)
        response_body = response.set_body.call_args[0][0]
        self.assertEqual(response_body, json.dumps(loggers))
        manager.get_service_logger_names.assert_called_with('logger', False)
        # Request with 'level' param
        mock_req = MagicMock(spec=Request)
        mock_req.get_params.return_value = {
            "level": "true",
            "identifier": "logger"
        }
        response = MagicMock()
        handler.on_get(mock_req, response)
        response_body = response.set_body.call_args[0][0]
        self.assertEqual(response_body, json.dumps(loggers))
        manager.get_service_logger_names.assert_called_with('logger', True)

    def test_on_post(self):
        manager = MagicMock()
        mock_req = MagicMock(spec=Request)
        mock_req.get_body.return_value = {
            "log_level": "ERROR",
            "logger_name": "logger"
        }
        mock_req.get_params.return_value = {"identifier": "service"}
        handler = ServiceLogHandler("", manager)
        response = MagicMock()
        handler.on_post(mock_req, response)
        manager.set_service_log_level.assert_called_with(
            'service', 'logger', 'ERROR')

    def test_on_put(self):
        manager = MagicMock()
        mock_req = MagicMock(spec=Request)
        mock_req.get_body.return_value = {
            "log_level": "ERROR",
            "logger_name": "logger"
        }
        mock_req.get_params.return_value = {"identifier": "service"}
        handler = ServiceLogHandler("", manager)
        response = MagicMock()
        handler.on_put(mock_req, response)
        manager.set_service_log_level.assert_called_with(
            'service', 'logger', 'ERROR')
