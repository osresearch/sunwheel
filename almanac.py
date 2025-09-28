#!/usr/bin/env python3
# Generate a declination table
#

from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan, modf
import datetime
import sys
import re

year = 2025

# Height of eye is 1.76 sqrt(H_e) in meters
def height_of_eye(H_e):
	return 1.76 * sqrt(H_e) * 6

# Refraction for normal conditions (10C 1010hPa)
# R = (n_air - 1) cot(theta)
# adjustment for non standard presure and temperature
def refraction(H_a, p=1010, t=10):
	r = 1/tan(radians(H_a + 7.31 / (H_a + 4.4)))
	f = p / (273+t) * 283/1010
	return f * r * -6


# minutes that the sun is ahead of noon
def equation_of_time(d,y=year):
	D = 6.24004077 + 0.01720197 * (365.25 * (y-2000) + d)
	return -7.659 * sin(D) + 9.863 * sin(2*D + 3.5932)

def julian(m,d,y=year):
	return int(datetime.date(y,m,d).strftime("%j"))
	

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
	degsym = "&deg;" if html else ' '

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
			descr = "%s %+4.1f %s" % (degfmt(decl, html=html), d * 60, ha)

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
					print("%-23s" % (' |'), end='')
				else:
					print(' | ' + month[day], end='')
			if html:
				print("</tr>")
			else:
				print('')


		if html:
#			print("<tr><td></td>")
#			for mon in ranges:
#				#              -DDXMM +0.d -mm:ss"
#				print("<td><tt>   Dec    d    GHA</tt></td>")
#			print("</tr>")
			print("</table>")
		else:
			print('')
