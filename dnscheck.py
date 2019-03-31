#!/usr/bin/env python

import sys, socket, dns.resolver, argparse

def domaingen(zones):
    if zones:
        for line in open(zones):
            if 'zone ' in line:
                yield line[line.find('"')+1:line.rfind('"')]
    else:
        for line in sys.stdin:
            yield line.strip()



def silent(*args, **kw):
    return

def output(*args, **kw):
    print(*args, file=sys.stderr, **kw)

def condemn(domain, condemned):
    condemned.append(domain)
    sys.stdout.write(domain + '\n')

def resolve(name):
    try:
        v4a = [x.address for x in dns.resolver.query(name, 'A')]
    except dns.resolver.NoAnswer:
        v4a = []
    except dns.resolver.NXDOMAIN:
        v4a = []
    try:
        v6a = [x.address for x in dns.resolver.query(name, 'AAAA')]
    except dns.resolver.NoAnswer:
        v6a = []
    except dns.resolver.NXDOMAIN:
        v6a = []
    return v4a + v6a

def nameserverips(name):
    ips = []
    for ns in dns.resolver.query(name, 'NS'):
        ips += resolve(ns.to_text())
    return ips

def main(hostname, out, zones, outzones):
    if not hostname:
        hostname = socket.gethostname()

    myips = resolve(hostname)
    if not myips:
        out("{} not found".format(hostname))
        sys.exit(1)

    condemned = []
    for domain in domaingen(zones):
        found = False
        try:
            ips = nameserverips(domain)
        except dns.resolver.NoNameservers:
            out("{} NO (error)".format(domain))
            condemn(domain, condemned)
            continue
        except dns.resolver.NoAnswer:
            out("{} NO (not found)".format(domain))
            condemn(domain, condemned)
            continue
        except dns.resolver.NXDOMAIN:
            out("{} NO (nxdomain)".format(domain))
            condemn(domain, condemned)
            continue
        for ip in ips:
            if ip in myips:
                out("{} YES ({} in {})".format(domain, ip, myips))
                found = True
                break
        if not found:
            out("{} NO ({} not in {})".format(domain, ips, myips))
            condemn(domain, condemned)

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
                if domain not in condemned:
                    of.write(zonedef)
            else:
                of.write(line)
        of.close()
        inz.close()


if __name__ == '__main__':
    a = argparse.ArgumentParser(description='Check if host is listed as nameserver for domain.')
    a.add_argument('hostname')
    a.add_argument('--silent', dest='out', action='store_const', const=silent, default=output)
    a.add_argument('--zones', dest='zones')
    a.add_argument('--outzones', dest='outzones')
    args = a.parse_args()
    main(args.hostname, args.out, args.zones, args.outzones)

