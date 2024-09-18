import dns.resolver
import dns.reversename


class DNSOps:
    def __init__(self):
        self.resolver = None
        self._init_resolver()

    def _init_resolver(self):
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = ["1.1.1.1", "8.8.8.8"]
        self.resolver.timeout = 2
        self.resolver.lifetime = 2

    def _get_ptr_records(self, ip):
        try:
            addr = dns.reversename.from_address(ip)
            answers = self.resolver.resolve(addr, "PTR")

            return [str(answer) for answer in answers]
        except:
            return []

    def _get_a_aaaa_records(self, domain):
        records = []
        for record_type in ["A", "AAAA"]:
            try:
                answers = self.resolver.resolve(domain, record_type)
                records.extend([str(answer) for answer in answers])
            except:
                pass

        return records

    def check_dns(self, ip_address):
        ptr_records = self._get_ptr_records(ip_address)

        if not ptr_records:
            return None

        result = []
        for ptr in ptr_records:
            forward_records = self._get_a_aaaa_records(ptr)
            result.append({ptr: {"resolves_back": ip_address in forward_records}})

        return result if result else None
