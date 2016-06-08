from unittest.mock import ANY, Mock

from niocore.common.executable_request import ExecutableRequest
from niocore.core.context import CoreContext
from niocore.testing.test_case import NIOCoreTestCase

from ..manager import LogManager
from ..core_handler import CoreLogHandler
from ..service_handler import ServiceLogHandler
from ..executor import LogExecutor


class TestLogManager(NIOCoreTestCase):

    def test_start(self):
        """ A handler is created and passed to REST Manager on start """
        rest_manager = Mock()
        rest_manager.add_web_handler = Mock()

        context = CoreContext([], [])
        manager = LogManager()
        manager.get_dependency = Mock(return_value=rest_manager)
        manager.configure(context)

        manager.start()
        rest_manager.add_web_handler.assert_called_with(ANY)
        self.assertEqual(2, len(rest_manager.add_web_handler.call_args_list))
        self.assertTrue(
            isinstance(rest_manager.add_web_handler.call_args_list[0][0][0],
                       CoreLogHandler))
        self.assertTrue(
            isinstance(rest_manager.add_web_handler.call_args_list[1][0][0],
                       ServiceLogHandler))

    def test_get_logger_names(self):
        manager = LogManager()
        response = manager.get_logger_names(add_level=False)
        self.assertIsInstance(response, list)
        self.assertGreater(len(response), 0)
        self.assertTrue("name" in response[0])
        self.assertTrue("level" not in response[0])

    def test_get_logger_names_add_level(self):
        manager = LogManager()
        response = manager.get_logger_names(add_level=True)
        self.assertIsInstance(response, list)
        self.assertGreater(len(response), 0)
        self.assertTrue("name" in response[0])
        self.assertTrue("level" in response[0])

    def test_set_log_level(self):
        # asserts set log level functionality by retrieving current loggers,
        # grabbing one of them, setting its level to a different value
        # and restoring it back
        manager = LogManager()
        response = manager.get_logger_names(add_level=True)
        if len(response):
            # grab first logger
            logger_name = response[0]['name']
            current_level = response[0]['level']
            # make sure to verify against a level that is not currently set
            if current_level == 'WARNING':
                target_level = 'ERROR'
            else:
                target_level = 'WARNING'
            manager.set_log_level(logger_name, target_level)
            # get log levels again and verify
            self._assert_level(manager, logger_name, target_level)

            # set back previous level
            manager.set_log_level(logger_name, current_level)
            self._assert_level(manager, logger_name, current_level)

    def _assert_level(self, manager, logger_name, level):
        response = manager.get_logger_names(add_level=True)
        # find logger
        for logger in response:
            if logger['name'] == logger_name:
                self.assertEqual(logger['level'], level)
                return

    def test_set_service_log_level(self):
        # asserts execute_request is invoked with expected parameters when
        # setting log level
        manager = LogManager()
        manager._service_manager = Mock()
        manager._service_manager.execute_request = Mock()
        self.assertEqual(manager._service_manager.execute_request.call_count,
                         0)
        manager.set_service_log_level("service1", "logger1", "DEBUG")
        self.assertEqual(manager._service_manager.execute_request.call_count,
                         1)
        (args, kwargs) = manager._service_manager.execute_request.call_args
        self.assertEqual(args[0], "service1")
        request = args[1]
        self.assertIsInstance(request, ExecutableRequest)
        self.assertEqual(request._type, LogExecutor)
        self.assertEqual(request._method, "set_log_level")
        self.assertEqual(request._args, ("logger1", "DEBUG"))

    def test_get_service_logger_names(self):
        # asserts execute_request is invoked with expected parameters when
        # retrieving logger names
        manager = LogManager()
        manager._service_manager = Mock()
        manager._service_manager.execute_request = Mock()
        self.assertEqual(manager._service_manager.execute_request.call_count,
                         0)
        add_level = True
        manager.get_service_logger_names("service1", add_level)
        self.assertEqual(manager._service_manager.execute_request.call_count,
                         1)
        (args, kwargs) = manager._service_manager.execute_request.call_args
        self.assertEqual(args[0], "service1")
        request = args[1]
        self.assertIsInstance(request, ExecutableRequest)
        self.assertEqual(request._type, LogExecutor)
        self.assertEqual(request._method, "get_logger_names")
        self.assertDictEqual(request._kwargs, {"add_level": True})
