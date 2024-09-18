import ipaddress
import logging
import signal
import sys

from flask import Flask, jsonify, request, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from paste.translogger import TransLogger
from waitress import serve
from werkzeug.exceptions import HTTPException

from . import __version__ as pkg_version
from .ipquery import IPQuery
from .log import set_root_logger


class WYA:
    def __init__(self):
        self.app = None
        self.limiter = None
        self.logger = None
        self.ipquery = None

    # flask
    @staticmethod
    def _http_status_handler(e):
        response = e.get_response()
        response.data = jsonify(
            {
                "error": e.name,
            }
        ).data
        response.content_type = "application/json"
        return response

    def _set_flask_app(self):
        self.app = Flask("wya")
        self.app.json.sort_keys = False
        self.app.json.compact = False
        self.app.json.ensure_ascii = False
        self.app.errorhandler(HTTPException)(self._http_status_handler)
        self.logger.info("created flask app")

    def _set_flask_routes(self):
        self.app.route("/", methods=["GET"])(self._get_client_ip)
        self.app.route("/<ip_address>", methods=["GET"])(self._get_ip_info)
        self.app.route("/ping", methods=["GET"])(self._ping)
        self.logger.info("created flask routes")

    # limiter
    def _set_limiter(self):
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["2000 per day", "50 per minute"],
            storage_uri="memory://",
        )

        self.limiter.init_app(self.app)
        self.logger.info("set rate limiter")

    # routes
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

    @staticmethod
    def _ping():
        return make_response("PONG\r\n")

    # signals
    def _signal_handler(self, signum, frame):  # pylint: disable=unused-argument
        signame = signal.Signals(signum).name

        if signame in ("SIGINT", "SIGTERM"):
            self.logger.info("caught %s, initiating graceful shutdown", signame)
            sys.exit(0)

        if signame in ("SIGHUP"):
            self.logger.info("caught SIGHUP, reloading GeoLite2 db's")
            self.ipquery.load_dbs()

    def _set_signal_handling(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGHUP, self._signal_handler)
        self.logger.info("set signal handling")

    # action
    def run(self):
        set_root_logger()
        self.logger = logging.getLogger("wya")
        self.logger.info("started wya ver. %s", pkg_version)

        self.ipquery = IPQuery()

        self._set_signal_handling()
        self._set_flask_app()
        self._set_limiter()
        self._set_flask_routes()

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
