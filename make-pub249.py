#!/usr/bin/python3
# Replace pub 249 with some diagrams
# Generate a circular web diagram of a given lattitude
# that allows Hc and Zn to be read directly.
import drawsvg as draw
from math import radians, cos, sin, acos, asin, degrees, log, floor, modf, atan2, sqrt, fabs, exp
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import black, red, HexColor
from contextlib import contextmanager
from almanac import haversine, ahaversine, frange, refraction, equation_of_time, julian, declination, declination_perp, compute_xy, height_of_eye, horizon_distance, stereographic_project, compute_hczn

gray = HexColor(0xC0C0C0)

pagesize = landscape(A4)
margin = 8*mm
pdf = canvas.Canvas('pub249.pdf', pagesize=pagesize)
pdf.setTitle("Sight Reduction Tables")

lat = 0
dec_max = 40
lha_max = 120
scale = 500
decimal = True

extra_thick = 3
thick = 1
thin = 0.1

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
	pdf.setLineWidth(thick)
	pdf.circle(0, 0, 5)
	for dec in range(-dec_max,dec_max+1):
		pts = []
		for lha in range(-lha_max,lha_max+1):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			pts += compute_xy(hc_scale(hc),zn+90)
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
			pts += compute_xy(hc_scale(hc),zn+90)

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
			*compute_xy(hc_scale(hc), zn+90),
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
			(x,y) = compute_xy(hc_scale(hc), zn+90)
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
		(x,y) = compute_xy(hc_scale(hc), 90)
		pdf_lines([x,y, x-l, y], width=w, color=c)

		if hc % 10 == 0 and hc != 0:
			pdf_text("%d" % (hc), 12,
				x-5, y-9,
				text_anchor="end",
				#class_="label",
			)
			
	return

def make_compass(r, draw_red = True, fs=15, faint=False):
	#g.append(draw.Circle(r=r, cx=0, cy=0, class_="thin"))

	pts = []
	for a in range(0,360):
		c = gray if faint else black
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
			*compute_xy(r,a+90),
			*compute_xy(r+l,a+90),
			],
			width = w,
			color = c,
		)
		pts += compute_xy(r,a+90)

	pdf_lines(pts, width=thick, color=gray if faint else black)

	# LHA=0 vertical line
	if draw_red:
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
		if not draw_red:
			offset *= -2
		pdf_text("%03d" % (a), fs,
			*compute_xy(r+10, (a+offset+90)),
			text_anchor=anchor,
			text_angle=rot-(a+offset),
			color=gray if faint else black,
		)

	# red going the other
	if not draw_red:
		return

	for a in range(0,360,10):
		if a <= 180:
			offset = -0.25
			rot = 270
			anchor = "start"
		else:
			offset = +0.25
			rot = 90
			anchor = "end"
		pdf_text("%03d" % (a), fs,
			*compute_xy(r+10, 180+(a+offset+90)),
			text_anchor=anchor,
			text_angle=rot-(a+offset),
			color = red,
		)
	return


def make_linearscale(r,max_v=60, side=1, steps=2, faint=False, fs=8):
	default_color = gray if faint else black

	pdf_lines([0,0, 0, r], width=thick, color=default_color)

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
			c = default_color
			l = text_offset
		elif v % (5*steps) == 0:
			w = thick * 0.5
			c = default_color
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

		pdf_text("%d" % (v//steps), fs,
			text_offset*side,
			lv,
			text_anchor=text_anchor,
			color=default_color,
		)

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
	x = 30 * mm
	y = 0

	def text(s):
		return pdf_text(s, fs, x, y, text_anchor="end")
	def line(x1=50,x2=0,y_offset=2):
		pdf_lines([x+x1,y+fs-y_offset,x+x2,y+fs-y_offset], width=thin)

	y += text("""
Date:
EOT:
Decl & d:
DR Lat/Lon:

Apparent Height=
+ Index Error:
- Eye / Dip:
- Refraction:""")

	line(50)
	y += text("Hs=\n+Lower/-Upper:")
	line(50)
	y += text("Ho=")

	line(-50,50,8)

	y += text("""
Time (UTC):
Hour Angle:
+ EOT:
DR Lon (+W/-E):""")
	line(50)

	y += text("LHA=")

	line(-50,50,8)

	y += text("""
Zn Lat/Dec/LHA:

Hu Lat/Dec/LHA:
Dec frac _____:
LHA frac _____:""")
	line(50)

	y += text("""Hc=
Ho=""")
	line(50)

	y += text("Intercept=")

	y += pdf_text("""Ho < Hc => Away
Ho > Hc => Towards""",
		fs-4, x, y,
		text_anchor="start",
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
		#make_checklist(lat)
		make_haversine_list(lat)

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


def make_worksheet(scale):
	# draw the list of things to fill in
	with pdf_translate(margin, pagesize[1] - 5):
		with pdf_scale(0.6):
			make_checklist(lat)

	# ensure that the big compass is in the center
	line_width = (pagesize[0]/2) - margin
	with pdf_translate(pagesize[0]/2, pagesize[1]/2):
		for y in range(0, 10):
			py = scale/2 * y
			if py > pagesize[1]/2:
				break
			pdf_lines([-line_width,py, +line_width,py],
				color=gray,
				width=thin,
			)
			pdf_lines([-line_width,-py, +line_width,-py],
				color=gray,
				width=thin,
			)
		pdf_lines([0, -pagesize[1]/2, 0, +pagesize[1]/2],
			color=gray,
			width=thin,
		)

		with pdf_scale(scale / 500 / 2):
			make_compass(500, draw_red=False, fs=15, faint=True)
			make_linearscale(500, max_v=60, side=-1, faint=True, fs=15)
			make_linearscale(500, max_v=100, side=+1, faint=True, fs=15)
	pdf.showPage()

def make_book(min_lat=0,max_lat=60):
	# title page
	# intro page
	# and then the latitude pages
	for lat in range(min_lat,max_lat):
		print("making %d" % (lat))
		make_latitude(lat)

# generate the pages of haversine and log(haversine)
# they are scaled to be in the range 0.00000 to 1.00000
def make_haversine(min_a = 0, max_a=90, steps=10):
	sz = 8
	line_sz = 7.5
	col_size = 35 * mm
	rows = 100
	x_offset = 2*margin
	y_offset = pagesize[0] - margin
	pdf.circle(0,0,10)

	def compute_axy(a, x_shift):
		ay = y_offset - (((a - min_a) * steps) % rows) * line_sz
		ax = x_offset + x_shift + (((a - min_a) * steps) // rows) * col_size
		return (ax,ay)


	for i in range(min_a*steps,max_a*steps,1):
		if i % rows == 0:
			# add a column header
#			pdf_text("θ  Hav   LogHav", sz,
#				x, y_offset - y + 2,
#				text_anchor="start",
#			)
#			pdf_lines([x, y_offset - y + 1, x+col_size-10*mm, y_offset - y + 1],
#				width=thin, color=black
#			)
			#pdf_lines([
			pass

		a = i / steps
		ac = 90 - a
		h = haversine(a)
		if h == 0:
			hl = 99999
		else:
			hl = log(h) * -10000
		if hl > 99999:
			hl = 99999;
		h *= 100000
		
		a_frac = i % steps
		ac_frac = modf(ac)[0] * 10

		(ax,ay) = compute_axy(a,0)
		if a_frac == 0:
			pdf_text("%d" % (a),
				sz+3,
				ax-8, ay,
				text_anchor="end",
			)
			width = thick
		else:
			pdf_text("%d" % (a_frac),
				sz,
				ax-5, ay,
				text_anchor = "end",
			)
			width = thin
		pdf_lines([ax-5, ay+sz/3, ax, ay+sz/3], width=width)

	def draw_loghav(i):
		lh = i / 1000
		a = degrees(ahaversine(exp(-lh)))
		if a < min_a or a > max_a:
			return
		(ax,ay) = compute_axy(a,0)
		if a < 20:
			txt = "%.0f" % (lh*10)
		else:
			txt = "%.2f" % (lh*10)
		pdf_text(txt, sz,
			ax+(5+30)/2, ay,
			text_anchor = "middle",
		)
		width = thin if i % 100 else thick
		pdf_lines([ax+5, ay+sz/3, ax, ay+sz/3], width=width)
		pdf_lines([ax+35, ay+sz/3, ax+30, ay+sz/3], width=width)
	for i in range(100,1720,5):
		draw_loghav(i)
	for i in range(1720,3500,10):
		draw_loghav(i)
	for i in range(3500,8000,100):
		draw_loghav(i)
	for i in range(8000,12000,500):
		draw_loghav(i)

	for i in range(0, 5000,10):
		h = i / 10000
		a = degrees(ahaversine(h))
		if a < min_a or a > max_a:
			return
		(ax,ay) = compute_axy(a,0)
		pdf_text("%.2f" % (h*100), sz,
			ax+40, ay,
			text_anchor = "start",
		)
		width = thin if i % 100 else thick
		pdf_lines([ax+35, ay+sz/3, ax+40, ay+sz/3], width=width)
		
		

# Generate the lookup table for the declinations at this latitude
def make_haversine_list(lat):
	x = 0
	sz = 9
	y = 0

	pdf_text("Dec CCL    Hav+   d   Hav-   d",
                #  xx 12345  12345 +xx  12345 xxx
		sz, 0, y, text_anchor="start")
	y -= sz

	for dec in range(0,23+1):
		cc = cos(radians(lat)) * cos(radians(dec))
		ccl = log(cc) * -10000
		h_same = haversine(lat - dec) * 100000
		h2_same = haversine(lat - dec - 1) * 100000
		h_contrary = haversine(lat + dec) * 100000
		h2_contrary = haversine(lat + dec + 1) * 100000

		d1 = (h2_same - h_same) / 10
		d2 = (h2_contrary - h_contrary) / 10

		pdf_text("%3d %05d  %05d %+02d  %05d %+02d" % (dec, ccl, h_same, d1, h_contrary, d2),
			sz,
			0,
			y  - dec * sz,
			text_anchor="start",
		)

def make_gha_table():
	sz = 6
	line_sz = 5.25
	y = 0
	col_x = 25*mm

	for x in [0,col_x]:
		pdf_text("UTC  Angle",
			sz + 2,
			x-10, y + sz + 1,
			text_anchor="start",
		)
		pdf_lines([x-10, y+sz, x+col_x-10*mm, y+sz], width=thin)
			
	for hour in range(0, 12):
		pdf_text("%02d:" % (hour), sz + 2,
			0, y,
			text_anchor="end",
		)
		pdf_text("%02d:" % (hour+12), sz + 2,
			col_x, y,
			text_anchor="end",
		)
		for minute in range(0,60,5):
			a1 = (hour + minute/60) * 15 - 180
			a2 = a1 + 180
			pdf_text("%02d % +7.2f" % (minute,a1),
				sz,
				0, y,
				text_anchor="start",
			)
			pdf_text("%02d % +7.2f" % (minute,a2),
				sz,
				col_x, y,
				text_anchor="start",
			)
			y -= line_sz
		y -= 3

def make_haversine_pages():
	# first page is angles 0 to 50
	with pdf_rotate(90):
		with pdf_translate(0,-pagesize[0]):
			make_haversine(0, 50)
	pdf.showPage()

	# second page is 50 to 90 and the UTC to hour angle chart
	with pdf_rotate(90):
		with pdf_translate(0,-pagesize[0]):
			make_haversine(50, 90)
		with pdf_translate(160*mm,-margin-5):
			make_gha_table()
	pdf.showPage()

make_haversine_pages()

def make_ccl_page():
	key = "ccl"
	pdf.bookmarkPage(key)
	pdf.addOutlineEntry("Cos(Dec)Cos(Lat) table", key, 0, 0)

	col_width = (pagesize[0]-margin) / 25
	col_offset = col_width
	row_offset = -10
	line_sz = (pagesize[1]-margin*2) / 64
	sz = 7
	def ccl_func(lat,dec):
		return log(cos(radians(lat)) * cos(radians(dec))) * -100

	# column header with the declination and the change
	# between each declination
	for dec in range(0,24):
		pdf_text("%d" % (dec),
			sz + 2,
			dec * col_width + col_offset - 5,
			0,
			text_anchor="end",
		)
		ccl = ccl_func(0,dec)
		ccl2 = ccl_func(0,dec+1)
		d = (ccl2 - ccl) * 100
		pdf_text("+%d" % (d),
			sz-2,
			dec * col_width + col_offset,
			0,
			text_anchor = "start",
		)

	y = row_offset
	for lat in range(0,60+1):
		pdf_text("%d" % (lat),
			sz + 2,
			0,
			y,
			text_anchor="end",
		)

		for dec in range(0,24):
			ccl = ccl_func(lat,dec)
			if ccl <= 0:
				ccl = 0
			pdf_text("%.2f" % (ccl),
				sz,
				dec * col_width + col_offset,
				y,
				text_anchor = "end",
			)

		if lat % 10 == 9 and lat != 59:
			pdf_lines([0, y-line_sz/2, 24 * col_width, y-line_sz/2], width=thin, color=gray)
			y -= line_sz * 1.5
		else:
			y -= line_sz


with pdf_translate(margin,pagesize[1]-margin):
	make_ccl_page()
pdf.showPage()

make_latitude(0)
make_latitude(52)
make_worksheet(6 * inch)
make_worksheet(3 * inch)
if decimal:
	make_times(100, 5)
else:
	make_times()

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


