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

from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan, floor, fabs, modf
import drawsvg as draw
import datetime
import sys
import re
from almanac import haversine, ahaversine, frange, refraction, equation_of_time, julian, declination, declination_perp, compute_xy, height_of_eye, horizon_distance, stereographic_project

deg_symbol = "°"
right_arrow = "➤"
output_file = "haversine.svg"

d = draw.Drawing(2000,1000, origin=(0,0))
d.append_css("""
@font-face {
        font-family: "B612 Regular";
        font-style: normal;
        src: url(fonts/B612-Regular.ttf);
}
@font-face {
        font-family: "B612 Italic";
        font-style: italic;
        src: url(fonts/B612-Italic.ttf);
}
text { font-family: "B612 Regular"; }
.italic { font-family: "B612 Italic"; }

.spinner {
	-webkit-transition: all 2s;
	-moz-transition: all 2s;
	transition: all 2s;
}
.extra_thick {
	fill: none;
	stroke: black;
	stroke-width: 2;
}
.thick {
	fill: none;
	stroke: black;
	stroke-width: 1;
}
.thin {
	fill: none;
	stroke: black;
	stroke-width: 0.5;
}
.extra_thin {
	fill: none;
	stroke: gray;
	stroke-width: 0.3;
}
.angle { 
	fill: black;
}
.red_angle {
	fill: red;
	font-family: italic;
}
""")


def draw_marker(label, radius, angle):
	g = draw.Group(transform="translate(%.3f)" % (radius))
	g.append(draw.Lines(
		0, 0,
		15, +5,
		25, +5,
		25, -5,
		15, -5,
		close=True,
		fill="black",
		stroke="none",
		transform="rotate(%.3f)" % (angle),
	))

	g.append(draw.Text(label, 14, 0, -12 if angle == 0 else +21 ,
		text_anchor="middle",
		fill="white",
		transform="rotate(%.3f)" % (90),
	))

	return g


# decimal degrees
def make_fractional_minutes(radius, include_marker=False, side=1, max_angle=1000, offset = 0):
	g = draw.Group(transform="rotate(%.3f)" % (offset))

	# skip the 0 since there is a marker
	for i in range(1,max_angle):
		a = 360 * i / 1000
		if side == 1:
			a = -a
		font_sz = None

		if i % 100 == 0:
			font_sz = 20
			c = "extra_thick"
			l = 15
		elif i % 10 == 0:
			font_sz = 15
			c = "thick"
			l = 10
		elif i % 5 == 0:
			c = "thin"
			l = 8
		else:
			c = "extra_thin"
			l = 5

		l1 = -l if side & 1 else 0
		l2 = +l if side & 2 else 0

		g.append(draw.Line(
			radius + l1, 0, radius + l2, 0,
			class_=c,
			transform="rotate(%.3f)" % (a),
		))

		if not font_sz:
			continue
		g.append(draw.Text(
			"%d" % (i // 10),
			font_sz,
			+10 if side & 2 else -10,
			(font_sz-2) if side & 2 else -2,
			class_="angle" if side & 2 else "red_angle",
			text_anchor="start" if side & 2 else "end",
			transform="rotate(%.3f) translate(%.3f 0) rotate(0)" % (a,radius),
		))
			
	if include_marker:
		g.append(draw_marker("0", radius, 0 if side & 2 else 180))

	return g

# log cosine for CCL computatoin
def make_log_cosine(radius, side=2, include_marker=True, division = 1.0, max_angle=60):
	g = draw.Group()

	# skip the 0 since there is a marker
	# TODO: fix the low digits
	for i in frange(30,10*10, 5) + frange(10*10, max_angle*10):
		lc = log(cos(radians(i/10)))
		whole = int(lc / division)
		frac = -((-lc) % division)
		#(frac,whole) = modf(lc)
		if whole != 0:
			print("uh oh", i, lc, frac, whole)
		a = -frac * 360 / division

		font_sz = None

		if int(i) % 100 == 0 and i > 100:
			font_sz = 20
			c = "extra_thick"
			l = 20
		elif int(i) % 50 == 0:
			font_sz = 15
			c = "extra_thick"
			l = 15
		elif int(i) % 10 == 0:
			if i > 100 or i == 80:
				font_sz = 15
			c = "thick"
			l = 15
		elif int(i) % 5 == 0:
			c = "thin"
			l = 10
		else:
			c = "extra_thin"
			l = 5

		l1 = -l if side & 1 else 0
		l2 = +l if side & 2 else 0

		g.append(draw.Line(
			radius + l1, 0, radius + l2, 0,
			class_=c,
			transform="rotate(%.3f)" % (a),
		))

		if not font_sz:
			continue
		g.append(draw.Text(
			"%d" % (i // 10),
			font_sz,
			+15 if side & 2 else -15,
			#(font_sz-2) if side & 2 else -2,
			font_sz-4,
			class_="angle" if side & 2 else "red_angle",
			text_anchor="start" if side & 2 else "end",
			transform="rotate(%.3f) translate(%.3f 0) rotate(0)" % (a,radius),
		))
			
	if include_marker:
		g.append(draw_marker("0", radius, 0 if side & 2 else 180))

	return g
	

def make_haversine_spiral(R,
	font_sz = 15,
	offset = 100,
	spacing = 5,
	max_angle = 90,
	log_scale = False,
	min_angle = 0,
	sides = 1,
	include_red = False,
	include_marker = False,
	division = 0.1,
):
	g = draw.Group()
	pts = []
	if log_scale:
		max_h = log(haversine(max_angle))
		min_h = log(haversine(min_angle))
		divs = int(min_h / division + 0.5)
		print(max_h, min_h, divs)
		def r_func(h):
			r_major = int(h / division)
			#return offset + (r_major  ((r_major-min_h-0.1)/range_h)*(R-offset-spacing*3)
			return offset + (divs - r_major) / divs * (R - offset - spacing - 25) + 25
		def a_func(h):
			r_minor = (h % division) / division
			return -r_minor*360
	else:
		# include space for the red numbers too
		max_h = haversine(max_angle)
		min_h = haversine(min_angle)
		divs = int(max_h / division)
		def r_func(h):
			r_major = int(h / division)
			return offset + (divs - r_major) / divs * (R - offset - spacing)
		def a_func(h):
			r_minor = (h % division) / division
			return r_minor*360

	for angle in frange(min_angle,max_angle+0.01,0.05):
		h = haversine(angle)
		if log_scale:
			h = log(h)
		r = r_func(h)
		a = a_func(h)
		(x,y) = compute_xy(r, a)
		pts += [x,y]

		(frac,whole) = modf(angle)
		gt = draw.Group(transform="rotate(%.3f) translate(%.3f 0)" % (a, r))
		frac = int(frac*100 + 0.5)

		if frac == 0:
			if int(angle) % 5 == 0 and angle != 0:
				c = "extra_thick"
				l = 20
				sz = font_sz + 5
			else:
				c = "thick"
				l = 15
				sz = font_sz
			gt.append(draw.Text("%d" % (angle) + (deg_symbol if log_scale else ""),
				sz,
				-7,
				-3 if log_scale else sz,
				class_="red_angle" if log_scale and int(angle) % 15 == 0 else "angle",
				text_anchor="end",
			))
			if include_red:
				gt.append(draw.Text("%d" % (90-angle),
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
			l = 10
			c = "thin"
		elif frac % 10 == 0:
			l = 5
			c = "thin"
		else:
			l = 4
			c = "extra_thin"

		gt.append(draw.Lines(
			-l if sides & 1 else 0, 0,
			0, 0, #+l if sides & 2 else 0, 0,
			class_=c,
		))

		g.append(gt)

	if include_marker:
		g.append(draw_marker("", offset, 0))
	g.append(draw.Lines(*pts, class_="thin"))
	return g


# Generate the helpers for adjsting the CCL by the fractional declination
def make_fractional_ccl(R):
	g = draw.Group()
	def ccl_step(dec): return log(cos(radians(dec)))-log(cos(radians(dec+1)))
	for decl in range(1,25):
		delta = ccl_step(decl) * 1000
		a = 4 * (decl-0.5) * 360 / 100
		g.append(draw.Text("%d" % (decl) + deg_symbol,
			12, -3, +0,
			class_="angle",
			text_anchor="end",
			transform="rotate(%.3f) translate(%.3f 0) rotate(90)" % (a, R),
		))
		pts = []
		for step in range(0,11):
			if step % 10 == 0:
				c = "thick"
				l = 10
			elif step % 5 == 0:
				c = "thin"
				l = 8
			else:
				c = "extra_thin"
				l = 5

			astep = a + step*delta/10
			pts += compute_xy(R, astep)

			g.append(draw.Lines(R, 0, R+l, 0,
				class_=c,
				transform="rotate(%.3f)" % (astep),
			))

		g.append(draw.Lines(*pts, class_="thin"))

	return g

def make_fractional_ccl2(R, max_h):
	g = draw.Group()
	def ccl_step(dec): return log(cos(radians(dec)))-log(cos(radians(dec+1)))
	# Horizontal lines every 5 degrees of declination
	for decl in range(5,26,5):
		delta = (ccl_step(decl) / -log(cos(radians(60)))) * 360
		pts = []
		for step in range(0,11):
			astep = -step*delta/10
			pts += compute_xy(R + decl * max_h/25, astep)
		if step % 10 == 0:
			c = "thick"
			l = 10
		elif step % 5 == 0:
			c = "thin"
			l = 8
		else:
			c = "extra_thin"
			l = 5

		g.append(draw.Lines(*pts, class_="thin"))

	for decl in [10, 15, 20]:
		g.append(draw.Text("%d" % (decl) + deg_symbol,
			10, 2, -(R + decl*max_h/25),
			class_="angle",
			text_anchor="start",
			transform="rotate(90)",
		))
	

	for step in range(0,11):
		pts = []
		for decl in range(0,26,1):
			delta = ccl_step(decl) * 1000
			astep = -step*delta/10
			pts += compute_xy(R + decl * max_h/25, astep)
		if step % 10 == 0:
			c = "thick"
			l = 10
		elif step % 5 == 0:
			c = "thin"
			l = 8
		else:
			c = "extra_thin"
			l = 5

		g.append(draw.Lines(*pts, class_=c))


	return g

def text_circle(s, sz, r, start=0, end=360, cx=0, cy=0, **kargs):
	p = draw.Path()
	(sx,sy) = compute_xy(r, start)
	(ex,ey) = compute_xy(r, end)
	p.M(sx,sy).A(r, r, 0, 0, 1, ex, ey)
	return draw.Text(s, sz, path=p, **kargs)


####
#### Front side
####
front = draw.Group(transform="translate(500 500)")
cut = 430
outer_cut = 500
outer = draw.Group(id="outer", class_="spinner")
inner = draw.Group(id="inner", class_="spinner")

# Cut lines and axle
inner.append(draw.Circle(0,0, cut, class_="thick"))
outer.append(draw.Circle(0,0, outer_cut, class_="thick"))
axle = draw.Circle(0,0, 5, class_="thick")
inner.append(axle)
outer.append(axle)

# Pointer with hidden half so it spins around the center
pointer = draw.Group(id="pointer", class_="spinner")
pointer.append(draw.Line(0,0, 500, 0, fill="none", stroke="blue", stroke_width=2))
pointer.append(draw.Line(0,0, -500, 0, fill="none", stroke="none", stroke_width=2))

inner_offset = 150
#inner.append(draw.Circle(0, 0, inner_offset, fill="black"))
inner_division = 1 / 14 + 0.0001 #haversine(35)
#inner_division = haversine(30)
inner.append(make_haversine_spiral(cut, min_angle=3, include_red=True, sides=3, offset=inner_offset, division = inner_division, font_sz=12))

# two loops of the haversine spiral for holding position on the outer ring
outer.append(make_haversine_spiral(outer_cut, min_angle=2, max_angle=44.4, sides=1, include_marker=True, offset=cut+35, division = inner_division))
#outer.append(make_fractional_minutes(cut, include_marker=True, side=2))

def front_instructions():
	for line in [
	"1. Pointer to Adjustment Angle on outer",
	"2. Inner index to pointer",
	"2. Inner index to pointer",
	"3. Pointer to DR LAT - Declination",
	"4. Read Hc from red angle",
	]:
		inner.append(text_circle(line, 20, inner_offset-5, 0, 180, text_anchor="start"))
		inner_offset -= 20

front.append(pointer)
front.append(outer)
front.append(inner)

####
#### Reverse side
#### inner disk is the same size as the outer
####
back = draw.Group(transform="translate(1500 500)")

outer = draw.Group(id="back_outer")
inner = draw.Group(id="back_inner")
inner.append(axle)
outer.append(axle)
inner.append(draw.Circle(0,0, cut, class_="thick"))
outer.append(draw.Circle(0,0, outer_cut, class_="thick"))


inner_offset = 100
#inner.append(draw.Circle(0, 0, inner_offset, fill="black"))
log_scale_limit = -log(cos(radians(60)))
inner.append(make_haversine_spiral(cut, log_scale=True, max_angle=135, min_angle=10.2, division=log_scale_limit, offset = inner_offset))

# Inside log cosine for declination
inner.append(make_log_cosine(cut, division=log_scale_limit, max_angle=25.01, side=1))
# outside log cosine for latitude
outer.append(make_log_cosine(cut, division=log_scale_limit))
#outer.append(make_fractional_minutes(cut, include_marker=True, side=2))

#outer.append(make_fractional_ccl(cut+25))
#outer.append(make_fractional_ccl2(cut, outer_cut - cut))

def add_instructions():
	text_r = (cut + outer_cut + 20) / 2
	outer.append(text_circle(
		"1. Align Local Hour Angle with Declination Fraction " + right_arrow + right_arrow,
		20, text_r,
		-90, -8,
		text_anchor="end",
	))

	outer.append(text_circle(
		"2. Move cursor to CCL for DR Lat and Declination " + right_arrow + right_arrow,
		20, text_r,
		10, 90,
		text_anchor="start",
	))

	outer.append(text_circle(
		"3. Carry and read Adjustment Angle from inner scale",
		20, text_r,
		90, 180,
		text_anchor="start",
	))

	outer.append(text_circle(
		"4. Compute DR Lat - Declination if needed",
		20, text_r,
		-179, -90,
		text_anchor="start",
	))

	for offset in [150, 215, 320, 372]:
		inner.append(draw.Text(right_arrow+right_arrow, 20, -offset, 0,
			class_="angle",
			transform="rotate(180)",
			text_anchor="end",
		))
		


#back.append(pointer)
back.append(outer)
back.append(inner)

d.append(front)
d.append(back)
d.save_svg(output_file)

