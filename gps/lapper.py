#!/usr/bin/python
"""
	calculate lap data from a gpx track
	still using some manual input at the moment
	ex: python lapper.py 2012-12-21T11:11:00Z 15 trackfile.gpx
"""

import sys, math, datetime, traceback
from lxml import etree

def ts(tss):
	"""
		parse gpx timestamp into a datetime
	"""
	return datetime.datetime.strptime(tss+"UTC", "%Y-%m-%dT%H:%M:%SZ%Z")

def metres(a, b):
	"""
		lat/long distance calculator
		based on http://en.wikipedia.org/wiki/Haversine_formula
		checked against http://www.movable-type.co.uk/scripts/latlong.html
		returns metres
	"""

	r = 6371000 # mean earth radius
	lat0, lon0 = float(a.attrib['lat']), float(a.attrib['lon'])
	lat1, lon1 = float(b.attrib['lat']), float(b.attrib['lon'])
	lat0r = math.radians(lat0)
	lat1r = math.radians(lat1)
	rlat = math.radians(lat1-lat0)
	rlon = math.radians(lon1-lon0)
	x = (math.sin(rlat/2)*math.sin(rlat/2) +
		math.sin(rlon/2)*math.sin(rlon/2)*math.cos(lat0r)*math.cos(lat1r))
	return 2*r*math.atan2(math.sqrt(x), math.sqrt(1-x))

def parse(xml, firstdate, dmetres):
	"""
		xml is etree element with gpx trackpoints

		firstdate is the timestamp where first lap starts, this also defines
		the starting line, or rather, circle

		dmetres is the radius of the starting circle
	"""
	origin = None # first gpx point
	timetag = None # full gpx trackpoint time tag name
	counter = None # lap counter
	outofcircle = None # state variable
	firstdatets = ts(firstdate)

	for tag in xml.getiterator():
		if tag.tag.endswith('}trkpt'): # deal with all trackpoints
			if origin is None: # find the first lap point based on timestamp and store it
				for c in tag:
					if c.tag.endswith('}time'):
						if (firstdatets - ts(c.text)).total_seconds() <= 0:
							timetag = c.tag # store the whole time's tag for easy access later
							origin = tag # remember origin trackpoint
							prevts = ts(tag.find(timetag).text) # remember lap start timestamp
							counter = 1 # start counting laps
							outofcircle = False
							break
				continue

			# calculate current distance from origin
			d = metres(origin, tag)
			# when we get out and back into the dmetres circle from origin, mark the next lap
			if not outofcircle and d > dmetres:
				outofcircle = True
			if outofcircle and d <= dmetres:
					# returns series of (lap counter, timestamp, lap time, distance from start)
					yield (counter, ts(tag.find(timetag).text),
						(ts(tag.find(timetag).text) - prevts), d)
					prevts = ts(tag.find(timetag).text)
					counter += 1
					outofcircle = False

if __name__ == '__main__':
	try:
		firstdate = sys.argv[1] # timestamp of the first point inside the first lap
		dmetres = int(sys.argv[2]) # radius of the starting point circle
		xml = etree.parse(file(sys.argv[3])) # gpx filename
	except Exception, msg:
		traceback.print_exc()
		print >>sys.stderr, 'usage: %s <timestamp of first lap start> <starting line detection threshold in metres> <gpx file name>' % sys.argv[0]
		sys.exit(1)

	for lap in parse(xml, firstdate, dmetres):
		print 'l=%03d t=%s d=%s m=%.1f' % tuple(lap)

