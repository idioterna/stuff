#!/usr/bin/python
"""
simple_http_check.py [-f myurlfile.urls] [-s]

fetches http/https urls defined in a text file
optionally compares to expected response
optionally searches for substring in body
optionally measures response times

file format is

name|url|expected http code|substring in page|warn timeout|critical timeout
mytest|http://mysite/|200|Copyright by my evil corp.|3|5
"""

import threading, urllib2, time, sys, os

DEFAULT_TIMEOUT = 30

WARNINGS = {}
ERRORS = {}
OK = {}

THREADS = []

def check_url(name, url, status, string, warn, crit):
	t0 = time.time()
	if crit:
		timeout = crit
	else:
		timeout = DEFAULT_TIMEOUT
	try:
		res = urllib2.urlopen(url, timeout=timeout)
		code = res.code
		body = res.read()
	except urllib2.HTTPError, msg:
		code = msg.code
	except urllib2.URLError, msg:
		try:
			msg = msg.reason.message or msg.reason.strerror
		except:
			pass
		ERRORS[name] = repr(msg)
		return
	except Exception, msg: # unknown error
		ERRORS[name] = repr(msg)
		return

	t = time.time() - t0

	if string and string not in body:
		ERRORS[name] = 'invalid content'
		return
	if crit and t > crit:
		ERRORS[name] = 'time crit %.1fs' % t
		return
	if warn and t > warn:
		WARNINGS[name] = 'time warn %.1fs' % t
		return
	if status and code != status:
		ERRORS[name] = 'expct HTTP %s, got %s' % (status, code)
		return
	OK[name] = '%.1fs' % t

def parsefile(filename):
	for line in open(filename):
		name, url, sstatus, string, swarn, scrit = line.strip().split('|')
		if sstatus:
			status = int(sstatus)
		else:
			status = 0
		if swarn:
			warn = float(swarn)
		else:
			warn = 0
		if scrit:
			crit = float(scrit)
		else:
			crit = 0
		yield name, url, status, string, warn, crit

def perform_checks(urlfile, force_serial=False):
	for probe in parsefile(urlfile):
		t = threading.Thread(target=check_url, name=probe[0], args=probe)
		THREADS.append(t)
		if force_serial:
			t.run()
		else:
			t.start()
		for t in THREADS:
			t.join()

if __name__ == '__main__':

	# file containing check definitions
	if '-f' in sys.argv:
		urlfile=sys.argv[sys.argv.index('-f')+1]
	else:
		urlfile=os.path.join(os.path.dirname(sys.argv[0]), 'simple_http_check.urls')
	if not os.path.isfile(urlfile):
		print 'CRIT check file %s does not exist' % urlfile
		sys.exit(2)

	# do not run tests in parallel
	if '-s' in sys.argv:
		force_serial=True
	else:
		force_serial=False

	# start threads and wait for results
	perform_checks(urlfile, force_serial)

	# print results
	if ERRORS:
		print 'CRIT',
		for name, error in ERRORS.iteritems():
			print '%s=%s,' % (name, error),
	if WARNINGS:
		print 'WARN',
		for name, warning in WARNINGS.iteritems():
			print '%s=%s,' % (name, warning),
	if OK:
		print 'OK',
		for name, fine in OK.iteritems():
			print '%s=%s,' % (name, fine),
	print

	# exit with an appropriate nagios plugin return code
	if ERRORS: sys.exit(2) # any errors are critical
	if WARNINGS: sys.exit(1) # if no errors occured, warnings are warnings
	if OK: sys.exit(0) # and OK is cool

