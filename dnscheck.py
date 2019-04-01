#!/usr/bin/env python

import sys, socket, dns.resolver, argparse, warnings

class DNSChecker:
    condemned = []

    def __init__(self, nameservers = None, silent = False):
        self.resolver = dns.resolver.Resolver()
        if nameservers:
            self.resolver.nameservers = nameservers
        else:
            self.resolver.nameservers = ['8.8.8.8', '1.1.1.1']
        self.silent = silent

    def domaingen(self, zones):
        if zones:
            for line in open(zones):
                if 'zone ' in line:
                    yield line[line.find('"')+1:line.rfind('"')]
        else:
            for line in sys.stdin:
                yield line.strip()



    def out(self, *args, **kw):
        if not self.silent:
            print(*args, file=sys.stderr, **kw)
        sys.stderr.flush()

    def condemn(self, domain, message=None):
        self.condemned.append(domain)
        sys.stdout.write(domain + '\n')
        if message:
            self.out(message)

    def resolve(self, name):
        try:
            v4a = [x.address for x in self.resolver.query(name, 'A')]
        except dns.resolver.NoAnswer:
            v4a = []
        except dns.resolver.NXDOMAIN:
            v4a = []
        try:
            v6a = [x.address for x in self.resolver.query(name, 'AAAA')]
        except dns.resolver.NoAnswer:
            v6a = []
        except dns.resolver.NXDOMAIN:
            v6a = []
        return v4a + v6a

    def nameserverips(self, name):
        ips = []
        try:
            for ns in self.resolver.query(name, 'NS'):
                ips += self.resolve(ns.to_text())
        except dns.exception.DNSException as e:
            warnings.warn(e, stacklevel=2)
        return ips

    def main(self, hostname, zones, outzones):
        if not hostname:
            hostname = socket.gethostname()

        myips = self.resolve(hostname)
        if not myips:
            self.out("{} not found".format(hostname))
            sys.exit(1)

        for domain in self.domaingen(zones):
            found = False
            self.out(domain, end=" ")
            try:
                ips = self.nameserverips(domain)
            except dns.resolver.NoNameservers:
                self.condemn(domain, "NO (error)")
                continue
            except dns.resolver.NoAnswer:
                self.condemn(domain, "NO (not found)")
                continue
            except dns.resolver.NXDOMAIN:
                self.condemn(domain, "NO (nxdomain)")
                continue
            for ip in ips:
                if ip in myips:
                    self.out("YES ({} in {})".format(ip, myips))
                    found = True
                    break
            if not found:
                self.condemn(domain, "NO ({} not in {})".format(ips, myips))

        if outzones:
            of = open(outzones, 'w')
            inz = open(zones)
            while True:
                line = inz.readline()
                if not line:
                    break
                if 'zone ' in line:
                    domain = line[line.find('"')+1:line.rfind('"')]
                    zonedef = line
                    while True:
                        zonedef += inz.readline()
                        if zonedef.count('{') == zonedef.count('}'):
                            break
                    if domain not in self.condemned:
                        of.write(zonedef)
                else:
                    of.write(line)
            of.close()
            inz.close()


if __name__ == '__main__':
    a = argparse.ArgumentParser(description='Check if host is listed as nameserver for domain.')
    a.add_argument('hostname')
    a.add_argument('--silent', dest='silent', action='store_true')
    a.add_argument('--zones', dest='zones')
    a.add_argument('--outzones', dest='outzones')
    a.add_argument('--nameservers', dest='nameservers', nargs='+')
    args = a.parse_args()
    dc = DNSChecker(args.nameservers, args.silent)
    dc.main(args.hostname, args.zones, args.outzones)

