from nomos.options import Options
from nomos.cmd import Cmd
from nomos import globalvar
from nomos.runner import NomosRunner


class Nomoser(object):

    def config(self, options):
        """Setting base site config"""
        group = options.group("Nomos settings")
        _ = group.define
        _('-u', '--url', default='http://localhost', help='The host of the http server url prefix (default %(default)r)')
        _('-d', '--debug', help='Open debug mode (default %(default)r)', action='store_true', default=False)
        _('-p', '--path', help='The test  nomos path (default %(default)r)', default="")
        _('-m', '--minix', help='The test  minix path list (default %(default)r)', default=[])
        _('-c', '--config', default=self.conf_path, help="config path (default %(default)r)", metavar="FILE")
        _("-v", "--version", help="Show nomos version 0.1")

        group = options.group("http settings")
        _ = group.define

        _('--http.timeout', default=30,
          help='http timeout setting: (default %(default)r)')
        _('--http.verify', help='The server TLS certificate (default %(default)r)', default=False)
        _('--http.cert.client_cert', default=None,
          help='Specify a local cert  (default %(default)r)')
        _('--http.cert.client_key', default=None,
          help='Specify a local cert  (default %(default)r)')

    def run(self, doc, conf_path=None):
        cmd = Cmd(conf_path)
        self.conf_path = conf_path
        config = cmd.parse_cmd(doc, [self])
        path = config.get("path")
        if path and not isinstance(path, list):
            path = path.split(",")
            config.set("path", path)

        minix = config.get("minix")
        if minix and not isinstance(minix, list):
            minix = minix.split(",")
            config.set("minix", minix)
        cert = None
        if config.get("http.cert.client_key") and config.get("http.cert.client_cert"):
            cert = (config.get("http.cert.client_cert"), config.get("http.cert.client_key"))

        globalvar.config.update(config)
        runner = NomosRunner(config.get("url"), config.get("path"),  timeout=config.get("http.timeout"), minixs=config.get("minix", []),
                             debug=config.get("debug"), cert=cert, verify=config.get("http.verify"))
        runner.run()


if __name__ == '__main__':
    runner = Nomoser()
    runner.run("Nomos")
