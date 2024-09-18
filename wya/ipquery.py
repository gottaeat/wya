import maxminddb

from .dnsops import DNSOps


class IPQueryConfig:
    def __init__(self):
        self.ip = None
        self.asn = None
        self.org = None
        self.hostname = None
        self.country = None
        self.city = None
        self.region = None
        self.tz = None
        self.loc = None


class IPQuery:
    def __init__(self):
        self.dns_ops = DNSOps()

        self.asn_db = None
        self.city_db = None
        self.load_dbs()

    @staticmethod
    def mkdict(ipquery):
        return {
            "ip": ipquery.ip,
            "asn": ipquery.asn,
            "org": ipquery.org,
            "hostname": ipquery.hostname,
            "country": ipquery.country,
            "city": ipquery.city,
            "region": ipquery.region,
            "loc": ipquery.loc,
            "tz": ipquery.tz,
        }

    def load_dbs(self):
        self.asn_db = maxminddb.open_database("GeoLite2-ASN.mmdb")
        self.city_db = maxminddb.open_database("GeoLite2-City.mmdb")

    def query(self, ip_address):
        # gen dicts
        city_dict = self.city_db.get(ip_address)
        asn_dict = self.asn_db.get(ip_address)

        # asn precheck
        if not asn_dict or "autonomous_system_number" not in asn_dict:
            return {"error": "not advertised"}

        ipquery = IPQueryConfig()

        # ip + asn
        ipquery.ip = ip_address
        ipquery.asn = f'AS{asn_dict["autonomous_system_number"]}'
        ipquery.org = asn_dict["autonomous_system_organization"]
        ipquery.hostname = self.dns_ops.check_dns(ip_address)

        # geo precheck
        if not city_dict:
            return ipquery

        # no country -> registered_country
        if "country" not in city_dict:
            if "registered_country" in city_dict:
                ipquery.country = city_dict["registered_country"]["iso_code"]

            return ipquery

        # country
        try:
            ipquery.country = city_dict["country"]["iso_code"]
        except KeyError:
            pass

        # city
        try:
            ipquery.city = city_dict["city"]["names"]["en"]
        except KeyError:
            pass

        # region
        if "subdivisions" in city_dict:
            subdivision_str = ""

            for subdivision in reversed(city_dict["subdivisions"]):
                subdivision_str += subdivision["names"]["en"] + "/"

            ipquery.region = subdivision_str[:-1]  # Remove the trailing "/"

        # loc
        try:
            loc_lat = city_dict["location"]["latitude"]
            loc_lon = city_dict["location"]["longitude"]

            ipquery.loc = f"{loc_lat},{loc_lon}"
        except KeyError:
            pass

        # tz
        try:
            ipquery.tz = city_dict["location"]["time_zone"]
        except KeyError:
            pass

        return ipquery
