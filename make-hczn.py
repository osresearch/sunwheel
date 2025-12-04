#!/usr/bin/python3
# Replace pub 249 with some diagrams
# Generate a circular web diagram of a given lattitude
# that allows Hc and Zn to be read directly.
import drawsvg as draw
from math import radians, cos, sin, acos, asin, degrees, log, floor, modf
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import black, red, HexColor
gray = HexColor(0xC0C0C0)

pagesize = A4
pdf = canvas.Canvas('pub249.pdf', pagesize=pagesize)

def haversine(x):
	return (1 - cos(x))/2
def ahaversine(y):
	if y < 0:
		y = 0
	if y > 1:
		y = 1
	return acos(1 - 2 * y)

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



lat = 52
dec_max = 60
lha_max = 170
scale = 450

extra_thick = 3
thick = 1
thin = 0.1

def pdf_lines(pts, width=1, color=black):
	pdf.setLineWidth(width)
	pdf.setStrokeColor(color)
	lines = []
	for i in range(0,len(pts)-2,2):
		lines += (pts[i:i+4],)
	pdf.lines(lines)


def pdf_text(txt, sz, x, y, text_angle=0, text_anchor="middle", font='Courier', color=black):
	pdf.saveState()
	pdf.translate(x,y)
	pdf.setFillColor(color)
	if text_angle:
		pdf.rotate(text_angle)
	pdf.setFont(font, sz)
	if text_anchor == "middle":
		pdf.drawCentredString(0, 0, txt)
	elif text_anchor == "end":
		pdf.drawRightString(0, 0, txt)
	else:
		pdf.drawString(0, 0, txt)
	pdf.restoreState()

def make_hczn(lat):
	#g = draw.Group()
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
			"%d" % (lha), 10,
			*compute_xy(hc_scale(hc), zn),
			text_angle = -90,
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
			pdf_text("%+d" % (dec), 10,
				x, y,
				#class_="label",
				text_anchor="end" if lha > 0 else "start",
				text_angle = -90,
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
			pdf_text("%d" % (hc), 10,
				x-5, y-8,
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
		pdf_text("%03d" % (a), 10,
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
		pdf_text("%03d" % (a), 10,
			*compute_xy(scale+10, 180+(a+offset)),
			text_anchor=anchor,
			text_angle=rot-(a+offset),
			color = red,
		)
	return

def make_height(r):
	g = draw.Group()
	g.append(draw.Circle(r=r, cx=0, cy=0, class_="thin"))

	for a in range(0,90*3):
		if a % (10*3) == 0:
			c = "extra-thick"
			l = 10
		elif a % 3 == 0:
			c = "thick"
			l = 8
		else:
			c = "thin"
			l = 5
		g.append(draw.Lines(
			*compute_xy(r,2*a/3),
			*compute_xy(r+l,2*a/3),
			class_=c,
			))

	for a in range(0,90,1):
		t = "%d" % (a)
		rot = 180
		anchor = "end"
		g.append(draw.Text(t, 10,
			0, -3,
			transform="rotate(%d) translate(%.3f) rotate(%d)" % (2*a+90, r+5, rot),
			text_anchor=anchor,
			dominant_baseline="bottom",
			class_="label",
		  ))
	return g

def make_chart(lat):
	g = draw.Group()
	g.append(draw.Text("Lat %d N" % (lat), 30,
		250,-450,
		class_="label",
		font_weight="bold",
	))
	g.append(draw.Text("Lat %d S" % (lat), 30,
		-250,-450,
		transform="rotate(180)",
		class_="label",
		font_weight="bold",
		text_anchor="end",
	))
	g.append(make_hczn(lat))
	g.append(make_compass(scale))

	g.append(make_logscale(800, 500, -400))
	g.append(make_logscale(800, 500, -400, direction=-1))
	return g

	#g.append(make_hc(lat))
	#g.append(make_height(scale))
	x = 0
	for a in range(0,90,15):
		g.append(make_linear_hc(lat, a, a+15, -25, 25, offset=(x,0)))
		x += 410

	g.append(draw.Circle(r=5, cx=0, cy=0, fill="#000"))

	return g


def make_lots():
	x = 0
	y = 0
	for lat in range(0,60,5):
		print(lat)
		g = draw.Group(transform="translate(%d %d) scale(0.3) translate(500 500)" % (x,y))
		g.append(make_chart(lat))
		d.append(g)

		x += 300
		if x > 900:
			x = 0
			y += 300

# just a vertical chart for the hc computation
# full page vertical angle from 0 to 90
def make_hc(lat):
	g = draw.Group()
	max_dec = 23
	min_hc = 0
	inner_r = 150

	scale_zn = lambda dec: (dec + max_dec) * (scale-inner_r) / (2*max_dec) + inner_r
	scale_hc = lambda hc: 180 - hc * 2

	for lha in range(0,180):
		pts = []
		for dec in range(-max_dec,max_dec+1):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			if hc < min_hc:
				continue
			pts += compute_xy(scale_zn(dec), scale_hc(hc))
		if len(pts) == 0:
			continue
		g.append(draw.Lines(*pts, class_="extra-thick" if (lha % 30 == 0) and (lha != 0) else "thick" if lha % 10 == 0 else "thin"))
	for dec in range(-max_dec,max_dec+1):
		pts = []
		for lha in range(0,180):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			if hc < min_hc:
				continue
			pts += compute_xy(scale_zn(dec), scale_hc(hc))
		if len(pts) == 0:
			continue

		if dec == 0:
			c = "extra-thick"
		elif dec % 5 == 0:
			c = "thick"
		else:
			c = "thin"

		g.append(draw.Lines(*pts, class_=c))

	for lha in [0,30,60,90]:
		for dec in range(-20,21,5):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0 or dec == 0:
				continue
			if hc < min_hc:
				continue
			g.append(draw.Text("%+d" % (dec), 10,
				*compute_xy(scale_zn(dec), scale_hc(hc)),
				text_anchor="end",
				class_="label" if dec > 0 else "red-label",
			))
	dec = -max_dec
	for lha in range(10,90,10):
		(hc,zn) = compute_hczn(lat, dec, lha)
		if hc < 0:
			continue
		if hc < min_hc:
			continue
		g.append(draw.Text("%d" % (lha), 10,
			*compute_xy(scale_zn(dec), scale_hc(hc)),
			class_="label",
		))
	return g


def make_linear_hc(lat,min_hc,max_hc,min_dec,max_dec, offset=(0,0)):
	g = draw.Group(transform="translate(%.3f %.3f)" % (offset[0], offset[1]))

	scale = 400
	scale_x = 0
	center_x = 800
	offset = 200
	mid_hc = (max_hc + min_hc) / 2
	hc_range = (max_hc - min_hc)

	def scale_hc(hc):
		return -(hc - mid_hc) / hc_range * scale*2
	def compute_pt(hc,zn):
		
		hc_y = scale_hc(hc)

		# the x is based solely on the declination
		pt_x = (dec - min_dec) / (max_dec - min_dec) * (center_x-offset) + offset
		#pt_x = zn/180 * (center_x - offset) + offset

		# the y solves for the point where the line from
		# (0,0) passes through (pt_x,pt_y) and (hc_y,center_x)
		# slope is hc_y / center_x
		# pt_y = pt_x * slope
		pt_y = pt_x * hc_y / center_x
		return (pt_x, pt_y)
	def compute_pt_lha(hc,zn):
		
		hc_y = -(hc - mid_hc) / hc_range * scale*2

		# the x is based solely on the LHA
		pt_x = (lha - 0) / 90 * (center_x-offset) + offset

		# the y solves for the point where the line from
		# (0,0) passes through (pt_x,pt_y) and (hc_y,center_x)
		# slope is hc_y / center_x
		# pt_y = pt_x * slope
		pt_y = pt_x * hc_y / center_x
		return (pt_x, pt_y)


	for dec in range(min_dec,max_dec+1):
		pts = []
		for lha in range(0,120+1):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < min_hc-1 or hc > max_hc + 1:
				continue

			pts += compute_pt(hc,zn)

		if len(pts) == 0:
			continue
		g.append(draw.Lines(*pts, class_="extra-thick" if dec == 0 else "thick" if dec % 5 == 0 else "thin"))

	for lha in range(0,120+1):
		pts = []
		for dec in range(min_dec,max_dec+1):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < min_hc-1 or hc > max_hc+1:
				continue

			pts += compute_pt(hc,zn)

		if len(pts) == 0:
			continue
		g.append(draw.Lines(*pts, class_="extra-thick" if lha % 10 == 0 else "thin"))

	g.append(draw.Circle(0, 0, 5, fill="#000"))
	g.append(draw.Line(center_x,-scale, center_x,+scale, class_="thick"))
	for hcp in range(min_hc*6, max_hc*6+1):
		hc_y = scale_hc(hcp/6)
		if hcp % 6 == 0:
			c = "extra-thick"
			l = 10
			g.append(draw.Text("%d" % (hcp//6), 10,
				center_x+10,
				hc_y,
			))
		elif hcp % 3 == 0:
			c = "thick"
			l = 8
		else:
			c = "thin"
			l = 5
		g.append(draw.Lines(
			center_x, hc_y,
			center_x+l, hc_y,
			class_=c,
		))

	return g

def make_logscale(r,x,y,max_v=60,direction=1):
	g = draw.Group(transform="translate(%.3f %.3f)" % (x,y))
	g.append(draw.Lines(0, 0, 0, r, class_="thick"))

	def scale_v(v):
		lv = (log(v) / log(max_v))
		if direction == 1:
			return lv * r
		return r - lv*r

	if direction > 0:
		text_anchor = "start"
		text_offset = +10
	else:
		text_anchor = "end"
		text_offset = -10
		
	for v in range(10,max_v*10+1):
		lv = scale_v(v/10)
		if v % 100 == 0:
			c = "extra-thick"
		elif v % 10 == 0:
			c = "thick"
		else:
			c = "thin"
		if v < 100 or v % 10 == 0:
			g.append(draw.Lines(0, lv, text_offset, lv, class_=c))
		if v % 10 != 0:
			continue
		elif v > 400:
			if v % 50 != 0:
				continue
		elif v > 200:
			if v % 20 != 0:
				continue
		g.append(draw.Text("%d" % (v//10), 10, text_offset, lv, class_="label", text_anchor=text_anchor))

	return g

def make_hc_table(lat,min_dec=-22,max_dec=22,min_lha=0,max_lha=90):
	# a4 size
	margin = 5 * mm
	width = pagesize[0] - 2 * margin
	height = pagesize[1] - 20*mm
	text_size = 5

	dec_width = width / (1 + max_dec - min_dec)
	dec_scale = lambda dec: (1+max_dec - dec) * dec_width + margin

	this_max_lha = 0
	dy = (height-20*mm) / 90


	# TODO: have the LHA numbers follow the bottom of the
	# Hc when they run out

	for dec in range(min_dec,max_dec+1):
		# check to see if this needs a column header
		(hc,zn) = compute_hczn(lat,dec,min_lha)
		if hc < 0.5:
			continue
		
		pdf.saveState()
		x = dec_scale(dec)
		y = 0
		pdf.translate(x, height)
		pdf_text("%+3d" % (dec), 7, 0, 0, text_anchor="end")
		vals = ''
		dels = ''
		for lha in range(min_lha, max_lha):
			(hc,zn) = compute_hczn(lat,dec,lha)
			(hc2,zn2) = compute_hczn(lat,dec,lha+1)

			# round hc up to nearest minute
			hc += 0.5 / 60
			if hc < 0:
				break

			# step between this and the next one
			d = floor((hc2 - hc) * 60)
			(mins,degs) = modf(hc)
			mins *= 60

			if lha % 10 == 0 and lha != 0:
				y -= dy/2
			y -= dy

			pdf_text(
				"% 2d %02d" %(degs,mins),
				text_size,
				0, y,
				text_anchor="end",
			)

			pdf_text(
				"%d" % (d),
				text_size-1,
				0, y,
				text_anchor="start",
			)
				

			if this_max_lha < lha:
				this_max_lha = lha


		pdf_lines([dec_width/3, 0, dec_width/3, y], width=thin, color=gray)
		pdf.restoreState()

	def draw_lha(lha_x):
		y = height
		pdf_text("LHA", 10, lha_x, y)
		for lha in range(min_lha,this_max_lha+1):
			if lha % 10 == 0 and lha != 0:
				y -= dy/2
			y -= dy
			pdf_text("%d" % (lha), text_size+1, lha_x, y)
	draw_lha(dec_scale(min_dec - 1))
	draw_lha(dec_scale(max_dec + 1))

	return
	

#center.append(make_chart(lat))
#d.append(make_hc_table(lat, pos=(1000,100)))
#d.append(make_lots())

#center.append(make_chart(lat))
#d.append(center)
#
#d.save_svg("hczn.svg")
#
#pdf = fpdf.FPDF(orientation="landscape", format="A4")
#pdf.add_page()
#pdf.image("hczn.svg")
#pdf.output("pub249.pdf")

make_hc_table(lat, min_lha=0, max_lha=90, min_dec=-23, max_dec=0)
pdf.showPage()
make_hc_table(lat, min_lha=0, max_lha=90, min_dec=0, max_dec=23)
pdf.showPage()

# finish up any tables from the other page
make_hc_table(lat, min_lha=90, max_lha=180, min_dec=0, max_dec=23)
pdf.showPage()

pdf.saveState()
pdf.translate(pagesize[0]/2,pagesize[1]/2)
scaling = (pagesize[0] - 15 * mm) / (2 * scale)
pdf.scale(scaling, scaling)
make_hczn(lat)
make_compass(scale)

pdf_text("Lat %d N" % (lat), 30, 0, scale + 100, text_anchor="middle")
pdf.rotate(180)
pdf_text("Lat %d S" % (lat), 30, 0, scale + 100, text_anchor="middle")
pdf.restoreState()


pdf.showPage()



pdf.save()

#d.save_png("hczn.png")


