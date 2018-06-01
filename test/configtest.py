from nomos.dsl import DslParser

import unittest
import os.path


class ConfigTest(unittest.TestCase):

    def test_config_from_file(self):
        conf_path = os.path.join(os.path.dirname(__file__), "conf")
        config = DslParser(conf_path, "config.txt")

        self.assertEqual(config.get("server.port"), 8880)
        self.assertEqual(config.get("server"), {
                         "port": 8880, "host": "localhost"})
        self.assertEqual(config.get("server.port1"), None)

    def test_get_list(self):
        conf = """list = [1,66]"""
        config = ConfigFactory.parse(conf)
        self.assertEqual(config.get_int_list("list"), [1, 66])

    def test_get_int(self):
        conf = """port = 123"""
        config = ConfigFactory.parse(conf)
        self.assertEqual(config.get_int("port"), 123)

    def test_get_string(self):
        conf = """host = "localhost" """
        config = ConfigFactory.parse(conf)
        self.assertEqual(config.get_string("host"), "localhost")

    def test_get_float(self):
        conf = """f = 1.25 """
        config = ConfigFactory.parse(conf)
        self.assertEqual(config.get_float("f"), 1.25)


class SelectConfigTest(unittest.TestCase):

    def setUp(self):
        self.config = SelectConfig()
        self.config.set("server.host", "localhost")
        self.config.set("server.port", 80)

    def test_get(self):
        self.assertEqual(self.config.get("server.port"), 80)
        self.assertIsNone(self.config.get("server.not_found"))
        # set default
        self.assertEqual(self.config.get("debug", True), True)

    def test_set(self):
        server_confg = self.config.get("server")
        self.assertEqual(server_confg['host'], 'localhost')
        self.assertEqual(server_confg['port'], 80)
        self.assertEqual(self.config.get("server.port"), 80)

    def test_update(self):
        self.config.set("server.host", "localhost")
        self.config.set("server.port", 80)
        config = {"server": {"host": "host2", "port": 90}, "debug": True}
        self.config.update(config)
        self.assertEqual(self.config.get("debug"), True)
        self.assertEqual(self.config.get("server.host"), "host2")

    def test_in(self):

        self.assertTrue("server" in self.config)
        self.assertFalse("server.not_found" in self.config)

    def test_delete(self):
        self.config.delete("server.port")
        self.assertIsNone(self.config.get("server.port"))
