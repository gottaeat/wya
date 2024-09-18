import ipaddress
import logging
import signal
import sys

from flask import Flask, jsonify, request
from paste.translogger import TransLogger
from waitress import serve

from . import __version__ as pkg_version
from .ipquery import IPQuery
from .log import set_root_logger


class WYA:
    def __init__(self):
        self.app = Flask("wya")
        self.app.json.sort_keys = False
        self.app.route("/", methods=["GET"])(self._get_client_ip)
        self.app.route("/<ip_address>", methods=["GET"])(self._get_ip_info)

        self.logger = None
        self.ipquery = None

    def _get_client_ip(self):
        if request.headers.get("X-Real-IP"):
            ip_address = request.headers.get("X-Real-IP")
        elif request.headers.get("X-Forwarded-For"):
            ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()
        else:
            ip_address = request.remote_addr

        return self._get_ip_info(ip_address)

    def _get_ip_info(self, ip_address):
        try:
            ip_obj = ipaddress.ip_address(ip_address)

            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
            ):
                return jsonify({"error": "invalid public ip address"}), 400
        except ValueError:
            return jsonify({"error": "invalid ip address"}), 400

        return jsonify(self.ipquery.mkdict(self.ipquery.query(ip_address)))

    def _signal_handler(self, signum, frame):  # pylint: disable=unused-argument
        signame = signal.Signals(signum).name

        if signame in ("SIGINT", "SIGTERM"):
            self.logger.info("caught %s, initiating graceful shutdown", signame)
            sys.exit(0)

        if signame in ("SIGHUP"):
            self.logger.info("caught SIGHUP, reloading GeoLite2 db's")
            self.ipquery.load_dbs()

    def _set_signal_handling(self):
        self.logger.info("set signal handling")
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGHUP, self._signal_handler)

    def run(self):
        set_root_logger()

        self.logger = logging.getLogger("wya")
        self.logger.info("started wya ver. %s", pkg_version)

        self._set_signal_handling()

        self.ipquery = IPQuery()

        access_logger = logging.getLogger("access")

        serve(
            TransLogger(self.app, logger=access_logger),
            host="0.0.0.0",
            port=8080,
            threads=32,
        )


def run():
    a = WYA()
    a.run()
