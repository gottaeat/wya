import ipaddress
import logging

from flask import Flask, jsonify, request
from waitress import serve
from paste.translogger import TransLogger

from .log import set_root_logger
from .geoquery import GeoQuery
from . import __version__ as pkg_version

set_root_logger(debug=True)
logger = logging.getLogger("wya")

gquery = GeoQuery()

app = Flask("wya")
app.json.sort_keys = False

def is_bogon(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
        )
    except ValueError:
        return True

@app.route("/", methods=["GET"])
def get_client_ip():
    if request.headers.get("X-Real-IP"):
        ip_address = request.headers.get("X-Real-IP")
    elif request.headers.get("X-Forwarded-For"):
        ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()
    else:
        ip_address = request.remote_addr

    return get_ip_info(ip_address)


@app.route("/<ip_address>", methods=["GET"])
def get_ip_info(ip_address):
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return jsonify({"error": "invalid IPv4 address"}), 400

    if is_bogon(ip_address):
        return jsonify({"error": "bogon"}), 400

    return jsonify(gquery.geo_to_dict(gquery.geoquery(ip_address)))


def run():
    logger.info("started wya ver. %s", pkg_version)
    serve(TransLogger(app), host='0.0.0.0', port = 6666, threads = 32)
