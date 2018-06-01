from nomos import cmd
import unittest


class CmdTest(unittest.TestCase):

    def test_get_file_opt(self):
        conf_path = os.path.join(os.path.dirname(__file__), "conf", "config.txt")
        c = cmd.Cmd(conf_path)
        config = c.get_file_opt()
        self.assertEqual(config.get("server.port"), 8880)

    def test_get_file_opt_not_found(self):
        c = cmd.Cmd("not_found")
        config = c.get_file_opt()
        self.assertEqual(len(config), 0)

    def test_parse_cmd(self):
        c = cmd.Cmd(conf_path)
        config = c.parse_cmd("test", [])
        self.assertEqual(config.get("server.port"), 8880)
