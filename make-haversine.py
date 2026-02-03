#!/usr/bin/env python3
# Generates the Haversine slide rule elements using SVG
# Front is a Haversine, rear is log(Haversine)
#
# Usage:
# Given DR Lat (LAT), Sun Declination (DEC), and Local Hour Angle (LHA)
# computes the expected height Hc using haversine's law.
# If LHA is less than 10 degrees, you probably want a meridian sight instead.
#
# On the log side:
# 1. Rotate the inner so that the declination in red lines up with
# the outer index.
# 2. Move the pointer to the DR Lat on the outer in black.
# 3. Rotate the inner so that the LHA is under the cursor
# 4. Move the pointer clockwise to the outer index, tracking if it crosses
# the inner index, in which case move to the next line in.
# 5. Read the Adjustment Angle from under the cursor and record it.
# This is ahav(hav(lha)*cos(lat)*cos(dec))
# The functions computed were ahav(exp(log(hav(lha)) + log(cos(lat)) + log(cos(dec))))
#
# Flip to the linear side.
# 1. Move the pointer to the outer index
# 2. Rotate the inner so that the Adjustment Angle is under the cursor.
# Make note of the carry number if there is one.
# 3. Move the pointer to the inner index
# 4. Rotate the inner so that the Dec - Lat value (ignoring the sign)
# is under the pointer.
# 5. Move the pointer clockwise to the outer index, tracking if it crosses
# the inner index, in which case move to the next line in.
# 6. Move in the additional carry number from the adjustment angle
# 7. Read the Hc from the red numbers on the spiral.

# It can also do the opposite, but takes some tweaks

from sliderule import *
#from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan, floor, fabs, modf
#import drawsvg as draw
import datetime
import sys
import re
#from almanac import haversine, ahaversine, frange, refraction, equation_of_time, julian, declination, declination_perp, compute_xy, height_of_eye, horizon_distance, stereographic_project

output_file = "haversine.svg"
output_a3_file = "haversine-a3.svg"


d = draw.Drawing(2000,1000, origin=(0,0), onload="drag_init(evt)")
d.append_css(css)
a3 = draw_a3()

# log cosine for CCL computatoin
def make_log_cosine(R,
	side=2,
	include_marker=True,
	division = 1.0,
	min_angle=0,
	max_angle=60,
	sz = 10,
):
	g = draw.Group()

	g.append(draw.Circle(0, 0, R, class_="thin"))

	# 
	angles = []
	angles += frange(min_angle, min(10, max_angle), 1/2)
	angles += frange(10, min(20, max_angle), 1/4)
	angles += frange(20, min(30, max_angle), 1/12)
	angles += frange(30, min(50, max_angle), 1/24)
	angles += frange(50, min(60, max_angle), 1/60)
	for angle in angles:
		lc = log(cos(radians(angle)))
		(a_frac,a_deg) = modf(angle)
		a_frac = int(a_frac*60 + 0.5)

		whole = int(lc / division)
		frac = -((-lc) % division)
		#(frac,whole) = modf(lc)
		if whole == 0:
			radius = R
		else:
			radius = R + 30
			#print("uh oh", i, lc, frac, whole)
		if side == 1:
			a = +frac * 360 / division
		else:
			a = -frac * 360 / division

		font_sz = None

		if a_frac == 0 and a_deg % 10 == 0: #int(i) % (10*steps) == 0 and i > 10*steps:
			font_sz = sz + 5
			c = "extra_thick"
			l = 25
		elif a_frac == 0 and a_deg % 5 == 0: # int(i) % (5*steps) == 0:
			font_sz = sz
			c = "extra_thick"
			l = 20
		elif a_frac == 0: # int(i) % (1*steps) == 0:
			if a_deg > 10 or a_deg == 8:
				font_sz = sz
			c = "thick"
			l = 20
		elif a_frac == 30: # int(i) % (steps//2) == 0:
			c = "thin"
			l = 20 if a_deg > 16 else 10
		elif a_frac % 10 == 0: #int(i) % (steps//10) == 0:
			c = "thin"
			l = 15
		elif a_frac % 5 == 0: #int(i) % (steps//10) == 0:
			c = "thin"
			l = 10
		else:
			c = "extra_thin"
			l = 8

		l1 = -l if side & 1 else 0
		l2 = +l if side & 2 else 0

		g.append(draw.Line(
			radius + l1, 0, radius + l2, 0,
			class_=c,
			transform="rotate(%.3f)" % (a),
		))

		if not font_sz:
			continue
		x_off = 16
		g.append(draw.Text(
			"%d" % (a_deg),
			font_sz,
			+x_off if side & 2 else -x_off,
			(font_sz-2) if side & 2 else -2,
			class_="angle" if side & 2 else "red_angle",
			text_anchor="start" if side & 2 else "end",
			transform="rotate(%.3f) translate(%.3f 0) rotate(0)" % (a,radius),
		))
			
	if include_marker:
		g.append(draw_marker("0", radius, 0 if side & 2 else 180))

	return g
	

def make_haversine_spiral(R,
	font_sz = 12,
	offset = 100,
	spacing = 10,
	max_angle = 90,
	log_scale = False,
	min_angle = 0,
	sides = 1,
	include_red = False,
	include_marker = False,
	offset_angle = 90,
	division = 0.1,
	direction = +1,
	divs = None,
	color_prefix = "",
):
	g = draw.Group()
	pts = []
	if log_scale:
		max_h = log(haversine(max_angle))
		min_h = log(haversine(min_angle))
		if not divs:
			divs = int(min_h / division-0.5)
		else:
			divs = -divs
		def r_func(h):
			r_major = int(h / division)
			#r_major = h / division
			#return offset + (r_major  ((r_major-min_h-0.1)/range_h)*(R-offset-spacing*3)
			return offset + (divs - r_major) / divs * (R - offset - spacing)
		def a_func(h):
			r_minor = (h % division) / division
			return -r_minor*360
	else:
		# include space for the red numbers too
		max_h = haversine(max_angle)
		min_h = haversine(min_angle)
		if not divs:
			divs = int(max_h / division+0.5)
		def r_func(h):
			r_major = int(h / division) # discrete levels
			#r_major = h / division # continuous spiral
			return offset + (divs - r_major) / divs * (R - offset - spacing)
		def a_func(h):
			r_minor = (h % division) / division
			return r_minor*360 * direction

	# highlight every other ring to make it easier to trace
	if False:
		for i in range(1,divs,2):
			div_r = offset + (divs - i) / divs * (R - offset - spacing) - 30/2
			ex = div_r * cos(radians(-2))
			ey = div_r * sin(radians(-2))
			g.append(draw.Path(
				stroke_width=30,
				stroke_opacity="0.20",
				stroke="#404040",
				fill="none",
			).M(div_r, 0)
			.A(div_r, div_r, 0, 1, 1, ex, ey)
			)

	angles = []
	if log_scale:
		angles += frange(min_angle,min(60,max_angle)+0.01, 1/60)
		angles += frange(60, min(125,max_angle)+0.01, 1/24)
		angles += frange(125, min(150,max_angle)+0.01, 0.125)
		angles += frange(150, min(165,max_angle)+0.01, 0.25)
		angles += frange(165, min(170,max_angle)+0.01, 0.5)
		angles += frange(170, min(180,max_angle)+0.01, 1)
	else:
		# they are very compressed at the start and end of the
		# spiral, but have more range in the middle
		angles += frange(min_angle,min(5,max_angle)+0.01, 1/4)
		angles += frange(5, min(15,max_angle)+0.01, 1/12)
		angles += frange(15, min(25,max_angle)+0.01, 1/24)
		angles += frange(25, min(100,max_angle)+0.01, 1/60)
		angles += frange(100, min(140,max_angle)+0.01, 1/24)

	for angle in angles: #frange(min_angle,max_angle+0.01,0.05):
		h = haversine(angle)
		if log_scale:
			h = log(h)
		r = r_func(h)
		a = a_func(h)
		(x,y) = compute_xy(r, a)
		pts += [x,y]

		(frac,whole) = modf(angle)
		gt = draw.Group(transform="rotate(%.3f) translate(%.3f 0)" % (a, r))
		frac = int(frac*60 + 0.5)
		l2 = 0

		if frac == 0:
			# whole number degrees
			c = "thick"
			l = 25
			l2 = 5
			sz = None
			x_off = -7

			if angle == 0:
				# no label
				c = "extra_thick"
			elif angle < 5:
				sz = font_sz - 3
				x_off = -15
			elif angle < 140 and int(angle) % 5 == 0:
				c = "extra_thick"
				l = 30
				l2 = 8
				sz = font_sz + 4
			elif angle <= 140:
				sz = font_sz
				x_off = -10
			elif angle < 160 and int(angle) % 2 == 0:
				sz = font_sz - 3
				x_off = -15
			elif 160 <= angle < 180 and int(angle) % 5 == 0:
				sz = font_sz - 3
				x_off = -15

			if sz:
				gt.append(draw.Text("%d" % (angle), # + (deg_symbol if not log_scale else ""),
					sz,
					x_off if sides & 1 else -x_off,
					-3 if log_scale or direction == -1 else sz,
					#class_="red_angle" if log_scale and int(angle) % 15 == 0 else "angle",
					class_=color_prefix + "angle",
					text_anchor="end" if sides & 1 else "start",
				))
			if sz and include_red:
				gt.append(draw.Text("%d" % (offset_angle - angle), # + (deg_symbol if not log_scale else ""),
					sz,
					x_off,
					-3 if not log_scale else sz,
					class_="red_angle",
					text_anchor="end",
				))

			major_r = int(h/division)
			if sz and include_red and major_r != 0:
				gt.append(draw.Text("+%d" % (major_r),
					font_sz-2,
					x_off, font_sz + sz,
					class_="angle",
					text_anchor="end",
				))
		elif frac == 30:
			l = 15
			l2 = 5
			c = "thin"
		elif frac % 10 == 0:
			l = 10
			c = "thin"
		elif frac % 5 == 0:
			l = 8
			c = "thin"
		else:
			l = 6
			c = "extra_thin"

		gt.append(draw.Lines(
			-l if sides & 1 else +l, 0,
			l2 if sides & 1 else -l2, 0, #+l if sides & 2 else 0, 0,
			class_=c,
		))

		g.append(gt)

	#for angle in frange(5,80,0.01):
	if False:
		h = sin(radians(angle))
		if log_scale:
			h = log(h)
		r = r_func(h*2)
		a = a_func(h*2)
		(x,y) = compute_xy(r, a)
		pts += [x,y]

		(frac,whole) = modf(angle)
		gt = draw.Group(transform="rotate(%.3f) translate(%.3f 0)" % (a, r))
		frac = int(frac*100 + 0.5)
		l2 = 0

		if frac == 0:
			# whole number degrees
			if int(angle) % 5 == 0 and angle != 0:
				c = "extra_thick"
				l = 30
				l2 = 8
				sz = font_sz + 5
			else:
				c = "thick"
				l = 25
				l2 = 5
				sz = font_sz
			gt.append(draw.Text("%d" % (angle) + (deg_symbol if log_scale else ""),
				sz,
				-7,
				-3 if log_scale else sz,
				class_="red_angle" if log_scale and int(angle) % 15 == 0 else "angle",
				text_anchor="end",
			))
			if include_red:
				gt.append(draw.Text("%d" % (offset_angle-angle),
					sz,
					-7,
					-3,
					class_="red_angle",
					text_anchor="end",
				))

			major_r = int(h/division)
			if include_red and major_r != 0:
				gt.append(draw.Text("+%d" % (major_r),
					font_sz-2,
					-7, font_sz + sz,
					class_="angle",
					text_anchor="end",
				))
		elif frac == 50:
			l = 15
			l2 = 5
			c = "thin"
		elif frac % 10 == 0:
			l = 10
			c = "thin"
		else:
			l = 6
			c = "extra_thin"

		gt.append(draw.Lines(
			-l if sides & 1 else 0, 0,
			l2, 0, #+l if sides & 2 else 0, 0,
			class_=c,
		))

		g.append(gt)

	if include_marker:
		g.append(draw_marker("", offset, 0))
	g.append(draw.Lines(*pts,
		#class_="extra_thick",
		class_="thick",
	))
	return g

####
#### Front side
####
cut = 420
outer_cut = 500
def make_front():
	outer = draw.Group(id="outer", class_="spinner", transform="rotate(0)")
	inner = draw.Group(id="inner", class_="spinner", transform="rotate(0)")

	# Cut lines and axle
	inner.append(draw.Circle(0,0, cut, fill="white", stroke="none"))
	outer.append(draw.Circle(0,0, outer_cut, fill="white", stroke="none"))

	inner.append(draw.Circle(0,0, cut, class_="thick"))
	outer.append(draw.Circle(0,0, cut, class_="thick"))
	outer.append(draw.Circle(0,0, outer_cut, class_="thick"))

	inner.append(draw_axle())
	outer.append(draw_axle())

	outer.append(text_circle("Haversine", 25, 100, -180, 0, text_anchor="middle"))

	now = datetime.datetime.today()
	outer.append(text_circle("%04d-%02d-%02d" % (now.year, now.month, now.day), 15, 80, -180, 0, text_anchor="middle"))

	inner_offset = 120
	#inner.append(draw.Circle(0, 0, inner_offset, fill="black"))
	#inner_division = 1 / 16 + 0.00051 #haversine(35)
	inner_division = 1 / 14 + 0.00051 #haversine(35)
	inner_division = haversine(35.8)
	#inner_division = haversine(30)
	inner.append(make_haversine_spiral(cut,
		min_angle=3,
		max_angle=120,
		include_red=True,
		sides=3,
		offset=inner_offset,
		division = inner_division,
		font_sz=12,
		divs=8,
	))
	log_scale_limit = -log(cos(radians(60.001)))
	#inner.append(make_haversine_spiral(cut, log_scale=True, max_angle=160, min_angle=10.2, division=log_scale_limit, offset = inner_offset, divs=7))

	inner.append(draw_marker("", cut, 180))
	outer.append(draw_marker("", cut, 0))

	if False: outer.append(text_circle(
	right_arrow3
	+ "Start on other side "
	+ right_arrow3
	+ "1. Red Declination to Outer Index "
	+right_arrow
	+ "2. Pointer to Inner Index "
	+right_arrow
	+ "3. LHA to Pointer "
	+right_arrow
	+ "4. Pointer Clockwise to Latitude on Outer"
	+right_arrow
	+ "5. Carry and read Adjust Angle"
	+right_arrow3,
		15,
		cut + 30,
		180,
		360,
		text_anchor="end",
	))

	if False: outer.append(text_circle(
	"This side"
	+ right_arrow
	+ "6. Pointer to Outer Index"
	+ right_arrow
	+ "7. Adjust Angle on inner to Pointer, note Carry"
	+right_arrow
	+ "8. Pointer to Inner Index "
	+right_arrow
	+ "9. Lat-Dec to Pointer "
	+right_arrow
	+ "10. Pointer CW to Outer Index "
	+right_arrow
	+ "11. Carry and read Hc in red",
		15,
		cut + 30,
		0,
		180,
		text_anchor="start",
	))

	inner.append(draw.Text("Hav(Z)", 20,
		inner_offset+0, 25,
		text_anchor="end",
		transform="rotate(-25)",
	))
	inner.append(draw.Text("Hav(90-Z)", 20,
		inner_offset+0, -2,
		text_anchor="end",
		transform="rotate(-25)",
		fill="red",
	))
	if False: inner.append(draw.Text("Hav(90-Hc) = Hav(Dec-Lat) +\nHav(LHA)*Cos(Dec)*Cos(Lat)", 12,
		0, inner_offset*.4,
		text_anchor="middle",
	))

	# the outer scales help both with keeping track of your place
	# as well as converting minutes to decimal degrees
	outer.append(draw.Line(cut, 0, outer_cut, 0, class_="extra_thick"))

	outer.append(draw.Circle(0, 0, outer_cut-5, class_="thin"))

	one_loop = 35.7
	outer.append(make_haversine_spiral(outer_cut-40, offset=cut, max_angle=one_loop, sides=2, include_red=False, spacing=+30, division = inner_division, direction=+1, color_prefix="red_"))
	outer.append(make_haversine_spiral(outer_cut+25, offset=outer_cut, max_angle=one_loop, sides=1, include_red=False, spacing=+30, division = inner_division, direction=-1, color_prefix=""))
	#outer.append(make_fractional_minutes(cut, side=2, font_sz=10, max_angle=60, include_red=True, include_marker=True))
	#outer.append(draw.Circle(0, 0, (outer_cut+cut)/2, class_="thin"))

	inner.append(text_circle("Linear Haversine", 20,
		inner_offset-25,
		-90-80, -90+80,
		class_="angle",
		text_anchor="middle",
	))
	inner.append(text_circle("hav(A)+hav(B)", 15,
		inner_offset-25,
		+90+45, +90-45,
		class_="angle",
		text_anchor="middle",
	))


	return (inner,outer)

####
#### Reverse side
#### inner disk is the same size as the outer
####
def make_back():
	outer = draw.Group(id="back_outer", class_="spinner", transform="rotate(0)")
	inner = draw.Group(id="back_inner", class_="spinner", transform="rotate(0)")
	inner.append(draw.Circle(0,0, cut, fill="white", stroke="none"))
	outer.append(draw.Circle(0,0, outer_cut, fill="white", stroke="none"))
	inner.append(draw_axle())
	outer.append(draw_axle())
	inner.append(draw.Circle(0,0, cut, class_="thick"))
	outer.append(draw.Circle(0,0, cut, class_="thick"))
	outer.append(draw.Circle(0,0, outer_cut, class_="thick"))

	outer.append(text_circle("Log Haversine", 25, 100, -180, 0, text_anchor="middle"))

	now = datetime.datetime.today()
	outer.append(text_circle("%04d-%02d-%02d" % (now.year, now.month, now.day), 15, 80, -180, 0, text_anchor="middle"))


	inner_offset = 120
	#inner.append(draw.Circle(0, 0, inner_offset, fill="black"))
	log_scale_limit = -log(cos(radians(60.001)))
	inner.append(make_haversine_spiral(cut,
		log_scale=True,
		max_angle=175,
		min_angle=7.2,
		font_sz = 10,
		division=log_scale_limit,
		include_red=True,
		offset_angle=360,
		offset = inner_offset,
		divs=8,
	))

	# Inside log cosine for declination
	#inner.append(make_log_cosine(cut, division=log_scale_limit, max_angle=25.01, side=1))
	# outside log cosine for latitude
	outer.append(draw.Line(cut, 0, outer_cut, 0, class_="extra_thick"))
	outer.append(make_log_cosine(cut+5, division=log_scale_limit, max_angle=60))
	#outer.append(make_log_cosine(cut+5, division=log_scale_limit, min_angle=60.1, max_angle=75.5, sz=8, side=2))

	outer.append(make_log_cosine(outer_cut-5, division=log_scale_limit, side=1, include_marker=False))
	#outer.append(make_fractional_minutes(outer_cut, side=1, font_sz=10))


	if False: inner.append(text_circle(left_arrow3 + "Local Hour Angle", 20, inner_offset - 18, -180, 0, text_anchor="middle"))
	if False: inner.append(draw.Text("Hav(LHA)*Cos(DEC)*Cos(LAT)", 12,
		0, inner_offset*.7,
		text_anchor="middle",
	))
	#inner.append(text_circle("Declination" + right_arrow3, 15, cut - 20, 80, 53, text_anchor="end", fill="red"))

	# repeat this one a few times
	for a in []: #[0, 120, 240]:
		outer.append(text_circle("Latitude" + right_arrow3, 15,
			cut + 20, a-45, a, text_anchor="end", fill="black"))

	outer.append(text_circle(left_arrow3 + "Hs Dec Hc", 12,
		cut+35, -45, -2, text_anchor="end", class_="red_angle",
	))
	outer.append(text_circle("Lat Hm" + right_arrow3, 12,
		cut+35, 2, +45, text_anchor="start", class_="angle",
	))

	inner.append(draw.Text("360-Z", 20,
		inner_offset+0, 25,
		text_anchor="end",
		transform="rotate(+13)",
		class_="red_angle",
	))
	inner.append(draw.Text("Z", 20,
		inner_offset+0, -2,
		text_anchor="end",
		transform="rotate(+13)",
		class_="angle",
	))

	inner.append(text_circle("Logarithmic Haversine", 20,
		inner_offset-20,
		-90-80, -90+80,
		class_="red_angle",
		text_anchor="middle",
	))
	inner.append(text_circle("hav(C)cos(a)cos(b)", 15,
		inner_offset-20,
		+90+45, +90-45,
		class_="red_angle",
		text_anchor="middle",
	))
	return (inner,outer)


front = draw.Group(transform="translate(500 500)")
(front_inner,front_outer) = make_front()
front.append(front_outer)
front.append(front_inner)
front.append(make_pointer("pointer"))

back = draw.Group(transform="translate(1500 500)")
(back_inner,back_outer) = make_back()
back.append(back_outer)
back.append(back_inner)
back.append(make_pointer("back_pointer"))

append_dragging(d)
d.append(front)
d.append(back)
d.save_svg(output_file)

append_a3(a3, outer_cut, cut, front_outer, front_inner, back_outer, back_inner, outer_diameter=172)
a3.append(draw.Image(1500, -800, 1000, 1000, path="spherical-triangle.svg", embed=True, transform="rotate(90) scale(0.45)"))
a3.save_svg("haversine-a3.svg")
