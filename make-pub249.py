#!/usr/bin/python3
# Replace pub 249 with some diagrams
# Generate a circular web diagram of a given lattitude
# that allows Hc and Zn to be read directly.
import drawsvg as draw
from math import radians, cos, sin, acos, asin, degrees, log, floor, modf, atan2, sqrt, fabs
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import black, red, HexColor
from contextlib import contextmanager
gray = HexColor(0xC0C0C0)

pagesize = landscape(A4)
margin = 8*mm
pdf = canvas.Canvas('pub249.pdf', pagesize=pagesize)
pdf.setTitle("Sight Reduction Tables")

lat = 0
dec_max = 40
lha_max = 150
scale = 500
decimal = True

extra_thick = 3
thick = 1
thin = 0.1

def haversine(x):
	return (1 - cos(x))/2
def ahaversine(y):
	if y < 0:
		y = 0
	if y > 1:
		y = 1
	return acos(1 - 2 * y)

# sin(Hc) = Sin(Lat) * Sin(Dec) + Cos(Lat) * Cos(Dec) * Cos(LHA))
# hav(90-Hc) = hav(LHA) * cos(lat) * cos(Dec) + hav(lat-dec)
def compute_hczn(lat,dec,lha):
	lat = radians(lat)
	dec = radians(dec)
	lha = radians(lha)
	hav_hc = haversine(lha) * cos(lat) * cos(dec) + haversine(lat - dec)
	#print(f"{lat=} {dec=} {lha=} => {hav_hc=}")
	hc = radians(90) - ahaversine(hav_hc)

	hav_zn = (cos(lat - hc) - sin(dec)) / (2 * cos(lat) * cos(hc))
	zn = degrees(ahaversine(hav_zn))

	# if the sun was to the west of us,
	# our local hour angle will be positive
	# and we have to adjust our computed heading
	if lha > 0:
		zn = 360 - zn

	return (degrees(hc),zn)


def compute_xy(r,a):
	a = radians(a)
	return (r * sin(a), r * cos(a))


@contextmanager
def pdf_translate(x,y):
	pdf.saveState()
	pdf.translate(x,y)
	yield
	pdf.restoreState()
@contextmanager
def pdf_rotate(a):
	pdf.saveState()
	pdf.rotate(a)
	yield
	pdf.restoreState()
@contextmanager
def pdf_scale(x,y=None):
	pdf.saveState()
	pdf.scale(x, y if y else x)
	yield
	pdf.restoreState()

# Apply a translation, a centered rotation, and a scale
# in that order
@contextmanager
def pdf_transform(x=0,y=0,a=0,cx=0,cy=0,sx=1,sy=None):
	pdf.saveState()
	pdf.translate(x,y)
	pdf.translate(cx,cy)
	pdf.rotate(a)
	pdf.translate(-cx,-cy)
	pdf.scale(sx, sy if sy else sx)
	yield
	pdf.restoreState()


def pdf_lines(pts, width=1, color=black):
	pdf.setLineWidth(width)
	pdf.setStrokeColor(color)
	lines = []
	for i in range(0,len(pts)-2,2):
		lines += (pts[i:i+4],)
	pdf.lines(lines)


def pdf_text(txt, sz, x, y, text_angle=0, line_size=None, text_anchor="middle", font='Courier', vert_align="bottom", color=black):
	if not line_size:
		line_size = sz

	with pdf_translate(x,y):
		pdf.setFillColor(color)
		if text_angle:
			pdf.rotate(text_angle)
		pdf.setFont(font, sz)

		if vert_align == "middle":
			y = -sz/2 + 2 # how to find baseline?
		elif vert_align == "top":
			y = -sz
		else:
			y = 0

		for line in txt.split("\n"):
			if text_anchor == "middle":
				pdf.drawCentredString(0, y, line)
			elif text_anchor == "end":
				pdf.drawRightString(0, y, line)
			else:
				pdf.drawString(0, y, line)

			y -= line_size
	return y

def make_hczn(lat):
	hc_scale = lambda hc: (90 - hc) * scale / 90
	for dec in range(-dec_max,dec_max+1):
		pts = []
		for lha in range(-lha_max,lha_max+1):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			pts += compute_xy(hc_scale(hc),zn)
		if len(pts) == 0:
			continue

		w = thin
		c = black
		if dec == 0:
			w = extra_thick
		elif dec % 5 == 0:
			w = thick
		elif dec == 23 or dec == -23:
			c = red
		else:
			c = gray
		pdf_lines(pts, width=w, color=c)
		#g.append(draw.Lines(*pts, class_=c))

	for lha in range(-lha_max,lha_max+1):
		if lha == 0:
			continue
		pts = []
		for dec in range(-dec_max,dec_max+1):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			pts += compute_xy(hc_scale(hc),zn)

		if len(pts) == 0:
			continue
		#g.append(draw.Lines(*pts, class_="thin" if lha % 10 else "thick"))
		if lha % 10 == 0:
			w = thick
			c = black
		else:
			w = thin
			c = gray
		pdf_lines(pts, width=w, color=c)

	# label the top of the chart
	for lha in range(-lha_max,lha_max+1,10):
		if lha == 0 or lha == 180 or lha == -180:
			continue

		(hc,zn) = compute_hczn(lat, dec_max+2, lha)
		if hc < 2:
			continue
		pdf_text(
			"%d" % (fabs(lha)), 15,
			*compute_xy(hc_scale(hc), zn),
			#text_angle = -90,
			text_anchor = "middle",
		)
			

	#for lha in range(0,lha_max+1,10):
		#if lha == 0 or lha == 180 or lha == -180:
			#continue
#
		#(hc,zn) = compute_hczn(lat, dec_max+3, lha)
		#if hc < 2:
			#continue
		#pdf_text("%+d" % (lha), 10,
			#*compute_xy(hc_scale(hc), zn),
			#text_anchor="middle",
		#)

	# label the declinations
	for lha in range(-lha_max,lha_max+1,30): #[-90,-60,-30,0,+30,+60,+90]:
		for dec in range(-dec_max+10,dec_max,10):
			if dec == 0 or lha == 180:
				continue
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < radians(1):
				continue
			(x,y) = compute_xy(hc_scale(hc), zn)
			pdf_text("%+d" % (dec), 15,
				x, y,
				#class_="label",
				text_anchor="end" if lha > 0 else "start",
				#text_angle = -90,
				#dominant_baseline="auto" if dec < 0 else "hanging",
			)

	# side ticks for the Zn readout
	for hc in range(0,90+1):
		if hc % 10 == 0:
			w = thick
			l = 10
			c = black
		elif hc % 5 == 0:
			w = thick
			l = 8
			c = black
		else:
			w = thin
			l = 5
			c = gray
		(x,y) = compute_xy(hc_scale(hc), 0)
		pdf_lines([x,y, x-l, y], width=w, color=c)

		if hc % 10 == 0 and hc != 0:
			pdf_text("%d" % (hc), 12,
				x-5, y-9,
				text_anchor="end",
				#class_="label",
			)
			
	return

def make_compass(r):
	#g.append(draw.Circle(r=r, cx=0, cy=0, class_="thin"))

	pts = []
	for a in range(0,360):
		c = black
		if a % 45 == 0:
			w = extra_thick
			l = 10
		elif a % 10 == 0:
			w = thick
			l = 10
		elif a % 5 == 0:
			w = thick
			l = 5
		else:
			w = thin
			l = 5
			c = gray
		pdf_lines([
			*compute_xy(r,a),
			*compute_xy(r+l,a),
			],
			width = w,
			color = c,
		)
		pts += compute_xy(r,a)

	pdf_lines(pts, width=thick)

	# LHA=0 vertical line
	pdf_lines([
		0,-r - 10,
		0,+r + 10,
		],
		width = extra_thick
	)

	# east/west lines are split so they
	# don't overlap with the grid
#	g.append(draw.Lines(
#		-r - 10,0,
#		-r + 50,0,
#		class_="extra-thick",
#	))
#	g.append(draw.Lines(
#		+r - 50,0,
#		+r + 10,0,
#		class_="extra-thick",
#	))

	pdf.setLineWidth(thick)
	pdf.circle(0, 0, 5)
	#g.append(draw.Circle(0,0, 10, fill="#000", stroke="none"))
#	pdf_lines([
#		-50,0,
#		+50,0,
#		],
#		width=extra_thick,
#	)

	# heading markings
	labels = {
		#0: ("N",90,"middle"),
		#90: ("E",0,"start"),
		#180: ("S",90,"middle"),
		#270: ("W",-180,"end"),
	}

	# black going one way
	for a in range(10,360+1,10):
		if a < 180:
			# put these above the mark
			offset = -0.25
			rot = 90
			anchor = "start"
		else:
			offset = 0.25
			rot = 270
			anchor = "end"
		pdf_text("%03d" % (a), 15,
			*compute_xy(scale+10, (a+offset)),
			text_anchor=anchor,
			text_angle=rot-(a+offset),
		)

	# red going the other
	for a in range(0,360,10):
		if a <= 180:
			offset = -0.25
			rot = 270
			anchor = "start"
		else:
			offset = +0.25
			rot = 90
			anchor = "end"
		pdf_text("%03d" % (a), 15,
			*compute_xy(scale+10, 180+(a+offset)),
			text_anchor=anchor,
			text_angle=rot-(a+offset),
			color = red,
		)
	return


def make_linearscale(r,max_v=60, side=1, steps=2):
	pdf_lines([0,0, 0, r], width=thick)
	def scale_v(v):
		return v / max_v * r

	text_offset = 10
	if side == 1:
		text_anchor = "start"
	else:
		text_anchor = "end"

	for v in range(0,int(max_v*steps)+1):
		lv = scale_v(v/steps)
		if v % (10*steps) == 0:
			w = thick * 0.5
			c = black
			l = text_offset
		elif v % (5*steps) == 0:
			w = thick * 0.5
			c = black
			l = text_offset - 4
		elif v % steps == 0:
			w = thick * 0.5
			c = gray
			l = text_offset - 4
		else:
			w = thin * 0.5
			c = gray
			l = text_offset - 6

		pdf_lines([0, lv, l*side, lv], width=w, color=c)
		if v % (5*steps) != 0:
			continue
		pdf_text("%d" % (v//steps), 8, text_offset*side, lv, text_anchor=text_anchor)

def make_scale(r,max_v=60,direction=1, logscale=None,extra_ticks=[]):
	pdf_lines([0,0, 0, r], width=thick)
	def scale_v(v):
		if logscale:
			lv = (log(v) / log(max_v))
		else:
			lv = v / max_v
		if direction == 1:
			return lv * r
		return r - lv*r

	if direction > 0:
		text_anchor = "start"
		text_offset = +10
	else:
		text_anchor = "end"
		text_offset = -10

	bottom = 10 if logscale else 0
		
	for v in range(bottom,max_v*10+1):
		lv = scale_v(v/10)
		c = black
		l = text_offset
		if v % 100 == 0:
			w = thick
		elif v % 10 == 0:
			w = thick
			c = gray
			l = text_offset - 4
		else:
			w = thin
			c = gray
			l = text_offset - 6

		if v == 450 or v == 550:
			l = text_offset

		if v < 100 or v % 10 == 0:
			pdf_lines([0, lv, l, lv], width=w, color=c)
		if v % 10 != 0:
			continue
		elif v > 400:
			if v % 50 != 0:
				continue
		elif v > 200:
			if v % 20 != 0:
				continue
		pdf_text("%d" % (v//10), 8, text_offset, lv, text_anchor=text_anchor)

	for tick in extra_ticks:
		lv = scale_v(tick)
		pdf_lines([0, lv, -text_offset, lv], width=thick)

def make_checklist(lat):
	fs = 10
	ls = 10
	x = 35 * mm
	y = 0
	y += pdf_text("""
Height
+IC
-Eye
-Temp/Refr
+Lower/-Upper
----
Ho
""",
		fs, x, y,
		text_anchor="end",
	)

	y += pdf_text("""
Time (UTC)
Noon Decl
Observed Decl

GHA
+ EOT
- DR Lon
----
LHA

Zn
DR Height
+/- d
---
Hc
""",
		fs, x, y,
		text_anchor="end",
	)

	y += pdf_text("Ho < Hc => Away",
		fs-1, x, y,
		text_anchor="end",
	)
	


def make_hc_table(lat,min_dec=-22,max_dec=22,min_lha=0,max_lha=90):
	# a4 size
	width = pagesize[0] - 2 * margin
	height = pagesize[1] - margin
	text_size = 6

	dec_width = width / (2 + max_dec - min_dec)
	dec_scale = lambda dec: (1+max_dec - dec) * dec_width + margin

	min_max_lha = 0
	max_max_lha = 0

	start_y = -5*mm
	dy = (height-35*mm) / (max_lha - min_lha)

	# TODO: have the LHA numbers follow the bottom of the
	# Hc when they run out

	# label the standalone pages and shift to make space
	if min_lha == 0:
		start_y = -15*mm
		pdf_text("Lattitude %d (%s Name)" % (
			lat,
			"Contrary" if min_dec < 0 else "Same"),
			18,
			pagesize[0]/2, pagesize[1] + start_y + 9,
			font="Helvetica",
			text_anchor="middle",
		)

	for dec in range(min_dec,max_dec+1):
		# check to see if this needs a column header
		(hc,zn) = compute_hczn(lat,dec,min_lha)
		if hc < 0.5:
			continue
		
		pdf.saveState()
		x = dec_scale(dec)
		y = start_y
		pdf.translate(x, height)

		# special case the "-0" for min dec
		txt = "%+3d" % (dec)
		if dec == 0 and max_dec == 0:
			txt = "-0"
		pdf_text(txt, 7, 0, y, text_anchor="end")
		vals = ''
		dels = ''
		for lha in range(min_lha, max_lha):
			(hc_orig,zn) = compute_hczn(lat,dec,lha)

			if min_dec < 0:
				dec2 = dec - 1
			else:
				dec2 = dec + 1
			(hc2_orig,zn2) = compute_hczn(lat,dec2,lha)

			# round hc up to nearest minute
			hc = floor(hc_orig*60) / 60
			hc2 = floor(hc2_orig*60) / 60
			if hc < 0:
				break

			# step between this and the next one
			d = floor((hc2 - hc) * 60)
			(mins,degs) = modf(hc)
			mins *= 60

			if lha % 10 == 0 and lha != 0:
				y -= dy/2
			y -= dy

			if decimal:
				d_decimal = (hc2_orig - hc_orig) * 100
				if d_decimal > 99:
					d_decimal = 99
				if d_decimal < -99:
					d_decimal = -99
				txt = " %5.2f" % (hc_orig)
				d_txt = "%+3d" % (d_decimal)
			else:
				txt = "% 2d %02d" % (degs,mins)
				d_txt = "%+d" % (d)

			pdf_text(txt,
				text_size,
				0, y,
				text_anchor="end",
			)

			pdf_text(
				d_txt,
				text_size-1,
				0, y,
				text_anchor="start",
			)
				

			if max_max_lha < lha and dec == max_dec:
				max_max_lha = lha
			if min_max_lha < lha and dec == min_dec:
				min_max_lha = lha


		pdf_lines([dec_width/3, start_y, dec_width/3, y], width=thin, color=gray)
		pdf.restoreState()

	def draw_lha(lha_x,max_lha):
		y = height + start_y
		if min_lha > max_lha:
			return
		pdf_text("LHA", 10, lha_x, y)
		for lha in range(min_lha,max_lha+1):
			if lha % 10 == 0 and lha != 0:
				y -= dy/2
			y -= dy
			pdf_text("%d" % (lha), text_size+1, lha_x, y)

	draw_lha(dec_scale(max_dec + 1), max_max_lha)
	draw_lha(dec_scale(min_dec - 1), min_max_lha)

	return

def make_latlon_scale(r, lat, steps=2, max_v=60):
	make_linearscale(r, max_v = max_v, side=1, steps=steps)
	make_linearscale(r*cos(radians(lat)), max_v = max_v, side=-1, steps=steps)


# A circular scale with lat on one side and lon on the other
# to allow measurement of minutes at this latitude
def make_latlon_circle(r, lat, steps=2, max_v = 60):
	lon_scale = cos(radians(lat))
	make_linearscale(r*lon_scale, max_v = max_v, side=1, steps=steps)
	if decimal:
		with pdf_translate(+22, 0):
			make_linearscale(r*lon_scale, max_v=60, side=1, steps=steps)

	for dr in range(5,max_v+1,5):
		pts = []
		for a in range(0,91,1):
			pr = dr * r / max_v
			(x,y) = compute_xy(pr,a)
			px = x * lon_scale
			#(hc,zn) = compute_hczn(lat, lat + del_lat/60, del_lon/60)
			pts += [-y,px]

			if a % 20 != 15 or a == 0 or a == 90 or dr == max_v or dr <= 10:
				continue

			# back compute the display angle
			a2 = degrees(atan2(y,px))
			r2 = sqrt(px*px+y*y)
			with pdf_rotate(a2):
				pdf_text("%d" % (dr),
					5,
					0,
					r2 + 2,
					color=gray,
					text_angle=90-(a2+a),
				)
					
		
		if dr % 10 == 0:
			w = thin
			c = black
		else:
			w = thin
			c = gray
		pdf_lines(pts, width=w, color=c)
			

	for a in range(10,90,10):
		(x,y) = compute_xy(r,a)
		w = thin
		c = gray
		pdf_lines([0,0, -y, x*lon_scale], width=w, color=c)


	pdf.rotate(90)
	make_linearscale(r, max_v=max_v, side=-1, steps=steps)
	if decimal:
		with pdf_translate(-22, 0):
			make_linearscale(r, max_v=60, side=-1, steps=steps)


def make_gunter(scale, lat):
	if decimal:
		max_v = 100
	else:
		max_v = 60
	make_scale(scale, max_v=max_v, logscale=True, extra_ticks = [cos(radians(lat)) * max_v])
	#pdf.rotate(180)
	#pdf.translate(0,-scale)
	#make_logscale(scale)
	

def make_tables(lat):
	dec = 23

	# negative declination pages
	make_hc_table(lat, min_lha=0, max_lha=60, min_dec=-dec, max_dec=0)
	pdf.showPage()

	# fixup page is half and half
	make_hc_table(lat, min_lha=60, max_lha=120, min_dec=-dec, max_dec=0)
	with pdf_transform(a=180, cx=pagesize[0]/2, cy=pagesize[1]/2):
		make_hc_table(lat, min_lha=60, max_lha=120, min_dec=0, max_dec=dec)
	pdf.showPage()

	# positive declination page, flipped to match above
	with pdf_transform(a=180, cx=pagesize[0]/2, cy=pagesize[1]/2):
		make_hc_table(lat, min_lha=0, max_lha=60, min_dec=0, max_dec=dec)
	pdf.showPage()

def make_chart(lat):
	# The page with the globe needs to rescale based on page size
	scaling = (pagesize[1] - 4 * margin) / (2 * scale)
	with pdf_transform(pagesize[0]/2+10*mm,pagesize[1]/2, 0, sx=scaling):
		make_hczn(lat)
		make_compass(scale)

		for hemi in ["N","S"]:
			if hemi == "S":
				pdf.rotate(180)
			pdf_text("Lat %d %s" % (lat,hemi),
				40,
				-scale+80, scale - 60,
				text_anchor="middle",
				font="Helvetica",
			)


	left = pagesize[0] - 2 * margin

	if decimal:
		max_v = 100
		small_steps = 0.5
	else:
		max_v = 60
		small_steps = 1

	with pdf_transform(2*margin, 2*margin, -90):
		make_latlon_circle(3*inch, lat, max_v=max_v)

	with pdf_translate(left, margin):
		make_gunter((6 + 1.5 + 0.15)*inch, lat)
	with pdf_translate(left - 15*mm, margin):
		make_latlon_scale(6*inch, lat, max_v=max_v)
	with pdf_translate(left - 15*mm, 6.15*inch + margin):
		make_latlon_scale(1.5*inch, lat, max_v=max_v, steps=small_steps)

	with pdf_translate(margin, pagesize[1] - margin):
		make_checklist(lat)

	pdf.showPage()

# 24-hour clock with GHA
def make_gha(r):
	inner_r = r - 40

	pdf.setLineWidth(thick)
	pdf.setStrokeColor(black)
	pdf.circle(0, 0, r)
	pdf.circle(0, 0, inner_r)
	pdf.circle(0, 0, 1)


	for hour in range(0,24):
		a = hour * 360/24 - 180
		with pdf_rotate(-a):
			pdf_text("%02d" % (hour),
				10, 0, r - 8,
				text_angle=a,
				text_anchor='middle',
				vert_align="middle",
			)

	for minute in range(0,24*60,10):
		a = minute * 360 / (24*60) - 180
		l = 5
		w = thin
		c = gray
		if minute % 60 == 0:
			# hour
			w = thick
			c = black
			l = 8
		elif minute % 30 == 0:
			c = black

		if a < -1:
			text_angle = -90
			text_anchor = "end"
			text_offset = +0.5
		else:
			text_angle = 90
			text_anchor = "start"
			text_offset = -0.5

		with pdf_rotate(-a):
			pdf_lines([0,r,0,r+l], color=c, width=w)

		(mins,degs) = modf(a)
		if mins < 0:
			mins *= -60
		else:
			mins *= +60

		sz = 5
		txt_offset = 6

		if a % 15 == 0:
			sz = 8
			txt = "%+.0f" % (a)
			txt_offset = 10
		elif decimal:
			txt = "%+.1f" % (a)
		else:
			txt = "%+d°%02d'" % (degs,mins)
		
		with pdf_rotate(-a + text_offset):
			pdf_text(txt,
				5 if a % 15 else 8,
				0, r+txt_offset,
				text_angle=text_angle,
				text_anchor=text_anchor,
			)

	for minute in range(0,60,1):
		a = minute * 360 / 60
		with pdf_rotate(-a):
			w = thin
			c = gray
			if a % 5 == 0:
				w = thick
				c = black
				pdf_text("%02d" % (minute),
					10, 0, inner_r - 8,
					text_angle=a,
					text_anchor='middle',
					vert_align="middle",
				)
			pdf_lines([0, inner_r, 0, inner_r+5], width=w, color=c)
		(mins,degs) = modf(minute * 15 / 60)
		mins *= +60
		sz = 5
		if mins == 0:
			txt = "%.0f" % (degs)
			sz = 8
		elif decimal:
			txt = "%.2f" % (minute * 15 / 60)
		else:
			txt = "%d°%02d'" % (degs,mins)

		if a < 180:
			text_angle = +90
			text_anchor = "start"
			text_offset = -0.5
		else:
			text_angle = -90
			text_anchor = "end"
			text_offset = +0.5

		with pdf_rotate(-a+text_offset):
			pdf_text(txt,
				sz, 0, inner_r + 6,
				text_angle=text_angle,
				text_anchor=text_anchor,
			)
			if a % 5 == 0:
				continue
			pdf_text("%02d" % (minute),
				5, 0, inner_r - 8,
				text_angle=text_angle,
				text_anchor=text_anchor,
			)
				
		
		


def make_times(scale=60,sz=8):
	key = "time60"
	pdf.bookmarkPage(key)
	pdf.addOutlineEntry("Times table", key, 0, 0)

	with pdf_translate(pagesize[0]*0.75,pagesize[1]*0.75-2*margin):
		make_gha(pagesize[1] * 0.25)

	#pdf.showPage()
	#return

	dx = (pagesize[0] - 2 * margin) / (scale + 0)
	dy = (pagesize[1] - 2 * margin) / (scale + 0)

	with pdf_translate(margin,pagesize[1] - margin):
		for a in range(1,scale+1):
			# left axis
			pdf_text("%2d" % (a), sz+1, dx*0.75 , -a*dy-1, font="Helvetica", text_anchor="end")
			# bottom axis
			pdf_text("%2d" % (a), sz+1, a * dx, -(scale+0.25)*dy, font="Helvetica", text_anchor="middle")
			for b in range(a,scale):
				pdf_text("%2d" % (a * b / scale),
					sz,
					a*dx, -b*dy,
					text_anchor="middle",
				)

			# don't include the last lines
			if a == scale-1:
				break

			x1 = dx
			x2 = (a + 0.5) * dx
			y1 = -a * dy - 2
			y2 = -(scale-1) * dy
			c = gray
			w = thin

			if a % 10 == 9:
				c = black
				w = thick
				y2 = -(scale+0.5)*dy
				x1 = 0
			elif a % 5 == 4:
				c = black

			# vertical lines (start mid way down)
			pdf_lines(
				[x2, y1, x2, y2],
				color=c, width=w,
			)

			# horizontal lines (start left axis)
			pdf_lines(
				[x1, y1, x2, y1],
				color=c, width=w)
			
	pdf.showPage()

def make_latitude(lat):
	key = "lat%d" % (lat)
	pdf.bookmarkPage(key)
	pdf.addOutlineEntry("Latitude %d" % (lat), key, 0, 0)

	make_chart(lat)
	make_tables(lat)

def make_book(min_lat=0,max_lat=60):
	# title page
	# intro page
	# and then the latitude pages
	for lat in range(min_lat,max_lat):
		print("making %d" % (lat))
		make_latitude(lat)

if decimal:
	make_times(100, 5)
else:
	make_times()
make_latitude(0)
make_latitude(52)

#pdf.saveState()
#pdf.translate(pagesize[0]/2,pagesize[1]/2+30 *mm)
#scaling = (pagesize[0] - 15 * mm) / (2 * scale)
#pdf.scale(scaling/2, scaling/2)
#pdf.translate(0,scale)
#make_round_hc(lat,100,-23,23,0,30)
#pdf.translate(0,-scale)
#make_round_hc(lat,100,-23,23,30,60)
#pdf.translate(scale,2*scale)
#make_round_hc(lat,100,-23,23,60,90)
#pdf.restoreState()

pdf.save()

#d.save_png("hczn.png")


