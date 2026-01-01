#!/usr/bin/env python3
# Generates the Haversine slide rule elements using SVG
# Front is a Haversine, rear is log(Haversine)
#

from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan, floor, fabs, modf
import drawsvg as draw
import datetime
import sys
import re
from almanac import haversine, ahaversine, frange, refraction, equation_of_time, julian, declination, declination_perp, compute_xy, height_of_eye, horizon_distance, stereographic_project

deg_symbol = "°"
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
def make_fractional_minutes(radius, include_marker=False, side=1, max_angle=1000):
	g = draw.Group()

	# skip the 0 since there is a marker
	for i in range(1,max_angle):
		a = 360 * i / 1000
		font_sz = None

		if i % 100 == 0:
			font_sz = 15
			c = "extra_thick"
			l = 15
		elif i % 10 == 0:
			font_sz = 12
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
			1, -8 if side & 2 else font_sz + 2,
			class_="angle" if side & 2 else "red_angle",
			text_anchor="start",
			transform="rotate(%.3f) translate(%.3f 0) rotate(90)" % (a,radius),
		))
			
	if include_marker:
		g.append(draw_marker("0", radius, 0))

	return g

	

def make_haversine_spiral(R,
	font_sz = 10,
	offset = 100,
	spacing = 5,
	max_angle = 90,
	log_scale = False,
	min_angle = 0,
	sides = 1,
	include_red = False,
	include_marker = True,
):

	g = draw.Group()
	pts = []
	if log_scale:
		max_h = log(haversine(max_angle))
		min_h = log(haversine(min_angle))
		range_h = max_h - min_h
		def r_func(h): return offset + ((modf(h)[1]-min_h-0.1)/range_h)*(R-offset-spacing*3)
		def a_func(h): return -modf(h)[0]*360
	else:
		# include space for the red numbers too
		max_h = haversine(max_angle)
		min_h = haversine(min_angle)
		#def r_func(h): return offset + (modf(h*10)[1]/10-min_h)*(R-offset+spacing*2+15)/(max_h-min_h)
		def r_func(h): return offset + (max_h-modf(h*10)[1]/10)*(R-offset-spacing*2-18)/max_h
		def a_func(h): return modf(h*10)[0]*360

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
				class_="angle",
				text_anchor="end",
			))
			if include_red:
				gt.append(draw.Text("%d" % (90-angle), sz,
					5,
					-3,
					class_="red_angle",
					text_anchor="start",
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
			+l if sides & 2 else 0, 0,
			class_=c,
		))

		g.append(gt)

	if include_marker:
		g.append(draw_marker("", R, 180 if sides % 2 else 0))
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
	for decl in range(5,26,5):
		delta = ccl_step(decl) * 1000
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

inner.append(make_haversine_spiral(cut, min_angle=4, include_red=True, sides=3))
outer.append(make_haversine_spiral(outer_cut+15, min_angle=2, max_angle=36.7, sides=1, include_marker=False))
outer.append(make_fractional_minutes(cut, include_marker=True, side=2))

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

inner.append(make_haversine_spiral(cut, log_scale=True, max_angle=120, min_angle=5.8))
inner.append(make_fractional_minutes(cut, include_marker=True, side=1, max_angle=251))
outer.append(make_fractional_minutes(cut, include_marker=True, side=2))

outer.append(make_fractional_ccl(cut+25))
outer.append(make_fractional_ccl2(cut, outer_cut - cut))

#back.append(pointer)
back.append(outer)
back.append(inner)

d.append(front)
d.append(back)
d.save_svg(output_file)

