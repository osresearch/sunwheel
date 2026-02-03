#!/usr/bin/env python3
# Generate a declination table
#

from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan, modf
import datetime
import sys
import re

year = 2026

def haversine(x):
	return (1 - cos(radians(x)))/2
def ahaversine(y):
	if y < 0: y = 0
	if y > 1: y = 1
	return degrees(acos(1 - 2 * y))

def compute_ccl(lat,dec):
	return log(cos(radians(lat)) * cos(radians(dec)))
def compute_adjust(lat, dec, lha):
	return ahaversine(haversine(lha) * cos(radians(lat)) * cos(radians(dec)))
	

def compute_xy(r,a):
	a = radians(a)
	return (r * cos(a), r * sin(a))

def frange(start, end, step=1):
	n_items = int(ceil((end - start) / step))
	items = []
	for i in range(n_items):
		items.append(start+i*step)
	return items

# Make a universal astrolabe projection
# https://www.neacsu.net/geodesy/snyder/5-azimuthal/sect_21/
def stereographic_project(r,lat,lon,clon=0):
	lat = radians(lat)
	lon = radians(lon)
	k0 = 1
	k = 2 * k0 / (1 + cos(lat) * cos(lon - clon))
	y = r * k * sin(lat)
	x = r * k * cos(lat) * sin(lon - clon)
	return (x,-y)

	lat = radians(lat)
	lon = radians(lon)
	slat = sin(lat)
	slon = sin(lon)
	clat = cos(lat)
	clon = cos(lon)

	x = clat * slon / (1 + slat)
	y = clat * clon / (1 + slat)
	return (x,y)

# sin(Hc) = Sin(Lat) * Sin(Dec) + Cos(Lat) * Cos(Dec) * Cos(LHA))
# hav(90-Hc) = hav(LHA) * cos(lat) * cos(Dec) + hav(lat-dec)
def compute_hczn(lat,dec,lha):
	#lat = radians(lat)
	#dec = radians(dec)
	#lha = radians(lha)
	hav_hc = haversine(lha) * cos(radians(lat)) * cos(radians(dec)) + haversine(lat - dec)
	#print(f"{lat=} {dec=} {lha=} => {hav_hc=}")
	hc = 90 - ahaversine(hav_hc)

	hav_zn = (cos(radians(lat - hc)) - sin(radians(dec))) / (2 * cos(radians(lat)) * cos(radians(hc)))
	zn = ahaversine(hav_zn)

	# if the sun was to the west of us,
	# our local hour angle will be positive
	# and we have to adjust our computed heading
	if lha > 0:
		zn = 360 - zn

	return (hc,zn)

# reverse the Hc Zn computation to produce LHA
# hav_hc = haversine(lha) * cos(radians(lat)) * cos(radians(dec)) + haversine(lat - dec)
# hav(lha) = (hav(90-hc) - hav(lat-dec)) / cos(lat) / cos(dec)
def compute_lha(lat, dec, hc):
	cc = cos(radians(lat)) * cos(radians(dec))
	hav_lha = (haversine(90-hc)  - haversine(lat-dec)) / cc
	return ahaversine(hav_lha)
	

# Height of eye is 1.76 sqrt(H_e) in meters
def height_of_eye(H_e):
	return 1.76 * sqrt(H_e)

# compute the height of eye required to see that distance in km,
# then convert that to a angle with height_of_eye
# cos(angle) = 
def horizon_distance(km):
	height = (km / 3.56972) ** 2
	return height_of_eye(height)

# Refraction for normal conditions (10C 1010hPa)
# R = (n_air - 1) cot(theta)
# adjustment for non standard presure and temperature
def refraction(H_a, p=1010, t=10):
	r = 1/tan(radians(H_a + 7.31 / (H_a + 4.4)))
	f = p / (273+t) * 283/1010
	return f * r


# minutes that the sun is ahead of noon
def equation_of_time(d,y=year):
	D = 6.24004077 + 0.01720197 * (365.25 * (y-2000) + d)
	return -7.659 * sin(D) + 9.863 * sin(2*D + 3.5932)

def julian(m,d,y=year):
	return int(datetime.date(y,m,d).strftime("%j"))

# The ephem library always wants UTC
def ephem_date(when):
	date = when.isoformat()
	date = re.sub(r"T"," ", date)
	date = re.sub(r"-","/", date)
	return date

# compute the lunar distance for a given date
def compute_ld(when):
	import ephem
	sun = ephem.Sun()
	moon = ephem.Moon()
	sun.compute(ephem_date(when))
	moon.compute(ephem_date(when))

	(ld,zn) = compute_hczn(
		degrees(sun.dec),
		degrees(moon.dec),
		degrees(sun.ha) - degrees(moon.ha),
	)

	return (
		90 - ld, zn,
		degrees(sun.dec),
		degrees(sun.ha),
		degrees(moon.dec),
		degrees(moon.ha),
	)


def correct_ld(old, hs, hm, hp):
	dz = compute_lha(hm, hs, old)
	rs = refraction(hs) / 60
	rm = refraction(hm) / 60
	(ld,_) = compute_hczn(hm + hp * cos(radians(hm))/60 - rm, hs - rs, dz)
	return ld
	

months = [
	["Jan",31],
	["Feb",28],
	["Mar",31],
	["Apr",30],
	["May",31],
	["Jun",30],
	["Jul",31],
	["Aug",31],
	["Sep",30],
	["Oct",31],
	["Nov",30],
	["Dec",31],
]


# related to the equation of time, the declination of the sun
# throughout the year for approximating the lattitude
# https://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations
# {\displaystyle \delta _{\odot }=-\arcsin \left[0.39779\cos \left(0.98565^{\circ }\left(N+10\right)+1.914^{\circ }\sin \left(0.98565^{\circ }\left(N-2\right)\right)\right)\right]}

def declination(d):
	return -degrees(asin(0.39779 * cos(radians(0.98565 * (d+10) + 1.914 * sin(radians(0.98565 * (d-2)))))))

# compute the perpendicular between two declination days
# for making pretty hash marks.
# there must be a better way to do this since we are already
# in polar space, but whatever we have to hard code it anyway
def declination_perp(d, a_func, r_func):
	d1 = a_func(d)
	d2 = a_func(d+1)

	r1 = r_func(d)
	r2 = r_func(d+1)

	(x1,y1) = compute_xy(r1, d1*6)
	(x2,y2) = compute_xy(r2, d2*6)

	a = atan2(y2-y1, x2-x1)
	return degrees(a) - d1*6 + 90

def degfmt(d, prec=1, html=False):
	rc = ''

	# this gets a little complicated if 0 < d < 1 since m will be negative
	# so force a different formatting on it
	if -1 < d < 0:
		return " -0X%04.1f" % (d * -60)

	(m,d) = modf(d)

	if m < 0:
		m = -m
	m *= 60
	
	rc += f'%+3dX%04.1f' % (d,m)
	return rc

if __name__ == "__main__":
	import ephem
	from datetime import datetime
	html = False
	decimal = False
	degsym = "&deg;" if html else ' '

	# TODO: use skyfield instead of ephem
	sun = ephem.Sun()

	year = datetime.today().year

	if len(sys.argv) > 1:
		year = int(sys.argv[1])

	cal = []
	for mon in range(0,12):
		month = []
		mdays = months[mon][1]
		if mdays == 28 and (year % 4 == 0) and (year % 100 != 0 or year % 400 == 0):
			mdays = 29

		prev_dec = 'XXXX'
		for day in range(0,mdays):
			sun.compute("%04d/%02d/%02d 12:00:00" % (year, mon+1, day+1))
			decl = degrees(sun.dec)
			sd = degrees(sun.radius)
			ha = degrees(sun.ha)

			# compute the change to the next hour
			# TODO: should compute the change over the whole day
			# and divide by 24
			sun.compute("%04d/%02d/%02d 13:00:00" % (year, mon+1, day+1))
			d = degrees(sun.dec) - decl

			# convert ha into minutes:seconds 
			if ha > 180:
				ha -= 360
			(ha_sec,ha_min) = modf(ha * (60 / 15))
			if ha_sec < 0:
				ha_sec = -ha_sec
			ha = "% 3d:%02d" % (ha_min, ha_sec * 60)

			#descr = "%s %+4.1f' %4.1f %s" % (degfmt(decl), d * 60, sd*60, ha)
			if decimal:
				descr = "%+7.3f %+3d %s" % (decl, d * 6000, ha)
			else:
				descr = "%s %+3d %s" % (degfmt(decl, html=html), d * 6000, ha)

			if descr.startswith(prev_dec):
				descr = '  " ' + descr[4:]
			else:
				prev_dec = descr[0:4]
			descr = re.sub("X", degsym, descr)
			#if html:
				#descr = re.sub(r"  ", " &nbsp;", descr)
			month.append(descr)
			#print("%02d/%02d"
		cal.append(month)


	for ranges in [range(0,6), range(6,12)]:
		if html:
			print("""
<style>
body { print-color-adjust: exact !important; }
table.alternate tr:nth-child(even) { background-color:#eee; }
table.alternate tr:nth-child(odd) { background-color:#fff; }
table.alternate td { text-align: end; padding: 0 8px; white-space:pre; }
</style>
<table class="alternate" style="break-after: page">
""")
			print("<tr>")
		for mon in ranges:
			mname = months[mon][0]
			if mon == 0 or mon == 6:
				if html:
					print(f"<th>{year}</th>")
				else:
					print("     ", end='')
					mname += " %04d" % (year)
			if html:
				print(f"<th>{mname}</th>")
			else:
				print("%-23s" % (mname), end='')
		if html:
			print("</tr>")
		else:
			print()

		for day in range(0,31):
			if html:
				print(f"<tr><td>{day+1}</td>")
			else:
				print("%2d" % (day+1), end='')
			for mon in ranges:
				month = cal[mon]
				if html:
					print(f"<td><tt>{month[day] if day < len(month) else ''}</tt></td>")
				elif len(month) <= day:
					if decimal:
						print("%-21s" % (' |'), end='')
					else:
						print("%-22s" % (' |'), end='')
				else:
					print(' | ' + month[day], end='')

			if html:
				print(f"<td>{day+1}</td></tr>")
			else:
				print("| %2d" % (day+1))


		if html:
#			print("<tr><td></td>")
#			for mon in ranges:
#				#              -DDXMM +0.d -mm:ss"
#				print("<td><tt>   Dec    d    GHA</tt></td>")
#			print("</tr>")
			print("</table>")
		else:
			print('')
