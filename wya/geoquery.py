import maxminddb

from .dnsquery import DNSQuery
dquery = DNSQuery()

class GeoQueryConfig:
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


class GeoQuery:
    def __init__(self):
        self.asn_db = None
        self.city_db = None
        self.init_dbs()

    def init_dbs(self):
        self.asn_db = maxminddb.open_database("GeoLite2-ASN.mmdb")
        self.city_db = maxminddb.open_database("GeoLite2-City.mmdb")

    def geoquery(self, ip_address):
        # gen dicts
        city_dict = self.city_db.get(ip_address)
        asn_dict = self.asn_db.get(ip_address)

        # asn precheck
        if not asn_dict or "autonomous_system_number" not in asn_dict:
            return {"error": "not advertised"}

        geoquery = GeoQueryConfig()

        # ip + asn
        geoquery.ip = ip_address
        geoquery.asn = f'AS{asn_dict["autonomous_system_number"]}'
        geoquery.org = asn_dict["autonomous_system_organization"]
        geoquery.hostname = dquery.check_dns(ip_address)

        # geo precheck
        if not city_dict:
            return geoquery

        # no country
        if "country" not in city_dict:
            if "registered_country" in city_dict:
                geoquery.country = city_dict["registered_country"]["iso_code"]

            return geoquery

        # country
        try:
            geoquery.country = city_dict["country"]["iso_code"]
        except KeyError:
            pass

        # city
        try:
            geoquery.city = city_dict["city"]["names"]["en"]
        except KeyError:
            pass

        # subdivisions (provinces etc.)
        if "subdivisions" in city_dict:
            subdivision_str = ""

            for subdivision in reversed(city_dict["subdivisions"]):
                subdivision_str += subdivision["names"]["en"] + "/"

            geoquery.region = subdivision_str[:-1]  # Remove the trailing "/"

        # coords
        try:
            loc_lat = city_dict["location"]["latitude"]
            loc_lon = city_dict["location"]["longitude"]

            geoquery.loc = f"{loc_lat},{loc_lon}"
        except KeyError:
            pass

        # timezone
        try:
            geoquery.tz = city_dict["location"]["time_zone"]
        except KeyError:
            pass

        return geoquery

    @staticmethod
    def geo_to_dict(geoquery):
        return {
            "ip": geoquery.ip,
            "asn": geoquery.asn,
            "org": geoquery.org,
            "hostname": geoquery.hostname,
            "country": geoquery.country,
            "city": geoquery.city,
            "region": geoquery.region,
            "loc": geoquery.loc,
            "tz": geoquery.tz,
        }
