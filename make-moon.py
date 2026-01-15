#!/usr/bin/env python3
# Moon increments and corrections
# Need to compute (14 deg 19 min / hour + d) * min past hour
# v goes from 0 - 18
# 
# 15 deg for the Sun
# 15 deg 2.4 for Aries
# 
# Measure the lunar distance, height of the moon and height of the sun.
# Add the moon and sun semi diameters to the lunar distnace
# Add the moon and sun semi diameters to the heights
# Compute the LHA between the sun and the moon given these heights as lat&dec
# and 90 minus the lunar distance with the nav wheel.
# - 
# Adjust the sun height for refraction
# Adjust the moon height for refraction and parallax (using this wheel)
# Compute the height with the navwheel using the adjusted heights and LHA
# 

from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan, floor, fabs, modf
import drawsvg as draw
import datetime
import sys
import re
from almanac import haversine, ahaversine, frange, refraction, equation_of_time, julian, declination, declination_perp, compute_xy, height_of_eye, horizon_distance, stereographic_project

deg_symbol = "°"
right_arrow = "➤"
right_arrow3 = right_arrow+right_arrow+right_arrow
left_arrow = "⮜"
left_arrow3 = left_arrow+left_arrow+left_arrow
output_file = "moon.svg"

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
def make_fractional_minutes(radius, include_marker=False, side=1, max_angle=100, offset = 0, font_sz = 15, include_red=False, divisions=10):
	g = draw.Group(transform="rotate(%.3f)" % (offset))

	for i in range(1 if include_marker else 0,max_angle*divisions):
		a = 360 * i / (max_angle*divisions)
		sz = None

		if i % (10*divisions) == 0:
			sz = font_sz + 2
			c = "extra_thick"
			l = 25
		elif i % divisions == 0:
			sz = font_sz
			c = "thick"
			l = 20
		elif i % (divisions//2) == 0:
			c = "thin"
			l = 15
		elif divisions == 60 and i % (divisions // 6) == 0:
			c = "thin"
			l = 12
		elif divisions == 60 and i % (divisions // 12) == 0:
			c = "thin"
			l = 8
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

		if not sz:
			continue
		xp = 1
		yp = sz+10 if side & 1 else -10
		g.append(draw.Text(
			"%d" % (i // divisions),
			sz,
			#+12 if side & 2 else -12,
			#(sz-1),
			+xp,
			+yp,
			class_="angle",
			#text_anchor="start" if side & 2 else "start",
			text_anchor="start",
			transform="rotate(%.3f) translate(%.3f 0) rotate(90)" % (a,radius),
		))

		if not include_red:
			continue
		g.append(draw.Text(
			"%d" % (i // divisions),
			sz,
			#+12 if side & 2 else -12,
			#(font_sz-2) if side & 2 else -2,
			#-2,
			-xp,
			+yp,
			class_="red_angle",
			text_anchor="end",
			transform="rotate(%.3f) translate(%.3f 0) rotate(90)" % (-a,radius),
		))
			
	if include_marker:
		g.append(draw_marker("0", radius, 0 if side & 2 else 180))

	return g


def text_circle(s, sz, r, start=0, end=360, cx=0, cy=0, **kargs):
	p = draw.Path()
	(sx,sy) = compute_xy(r, start)
	(ex,ey) = compute_xy(r, end)
	p.M(sx,sy).A(r, r, 0, 0, 1 if start < end else 0, ex, ey)
	return draw.Text(s, sz, path=p, **kargs)


def make_moon(R):
	g = draw.Group()
	offset = 125
	extra1 = 60 - 19 # sun
	extra2 = 62.43 - 19 # aries
	# log looks nicer?
	#def r_func(v): return R - 30 - (R-offset) * (log(v)/log(23))
	def r_func(v):
		if v <= 20:
			return offset + (R-offset) * v / 25
		if v < extra1:
			return offset + (R-offset) * 20 / 25 + (v - 20) * 1
		return offset + (R-offset) * 20 / 25 + (extra1 - 20) * 1 + (v - extra1) * 8
	for m in frange(0,60.01,0.25):
		pts = []
		#for v in frange(1,extra2+0.09,0.1):
		for v in frange(1,21):
			if v > 20 and m < 2:
				continue
			gha = 14 + (19+v)/60  # deg/hour
			a = (gha * m/60) / 15 * 360
			pts += compute_xy(r_func(v), a)
		if m % 10 == 0:
			c = "extra_thick"
		elif m % 5 == 0:
			c = "thick"
		elif m % 1 == 0:
			c = "thin"
		else:
			c = "extra_thin"
		g.append(draw.Lines(*pts,
			class_=c,
		))

	#for v in frange(1,20+1) + [extra1, extra2]:
	for v in range(1,20+1):
		pts = []
		for m in frange(0,60.01,0.1):
			if v > 20 and m < 2:
				continue
			gha = 14 + (19+v)/60  # deg/hour
			a = (gha * m/60) / 15 * 360
			pts += compute_xy(r_func(v), a)
		if v % 10 == 0 or v == extra1 or v == extra2:
			c = "extra_thick"
		elif v % 5 == 0:
			c = "thick"
		elif v > 20:
			continue
		else:
			c = "thin"
		g.append(draw.Lines(*pts,
			class_=c,
		))
			
	return g


# The lunar distance changes by +/-12 degrees per day,
# so a multiplication nomograph can be used to compute the
# time based on the distance between the moon and some other object.
# this scale helps with computing that time.
def make_lunar_dist(R):
	g = draw.Group()
	offset = 150
	min_d = 25
	max_d = 35
	#def r_func(d,m): return offset + (R - offset) * (max_d-d) / 10
	def r_func(d,m): return offset + (R - offset) * (d-min_d) / 10
	def a_func(d,m): return m * d / 100 / 6

	for d in range(min_d,max_d+1):
		pts = []
		pts2 = []
		for m in range(0, 60*60+1, 1):
			a = a_func(d,m)
			r = r_func(d,m)
			pts += compute_xy(r, a)
			pts2 += compute_xy(r, -a)

			if False and m % (60*10) == 0 and d % 2 == 0:
				g.append(draw.Text("%d" % (d), 12,
					*compute_xy(r, a),
					class_="red_angle",
				))
					
		if d == 30:
			c = "extra_thick"
		else:
			c = "thin"
		g.append(draw.Lines(*pts,
			class_=c
		))
		#g.append(draw.Lines(*pts2, class_=c))

	for m in range(0, 60*60+1, 30):
		pts = []
		pts2 = []
		for d in frange(min_d,max_d+0.01,0.1):
			a = a_func(d,m)
			pts += compute_xy(r_func(d,m), a)
			pts2 += compute_xy(r_func(d,m), -a)
		if m % (60*10) == 0 and m != (60*60) and m != 0:
			c = "extra_thick"
		elif m % (60*5) == 0:
			c= "thick"
		elif m % 60 == 0:
			c = "thin"
		else:
			c = "extra_thin"
		#g.append(draw.Lines(*pts2, class_=c))
		g.append(draw.Lines(*pts, class_=c))

		if m % (60*5) != 0 or m == 0 or m == 60*60:
			continue

		# add some labels
		for label_d in [(max_d*2+min_d)/3, min_d-1.6]:
			pts = []
			for d in range(1,5):
				pts += compute_xy(r_func(label_d+d, m+3), a_func(label_d+d, m+3))
			path = draw.Lines(*pts)
			g.append(draw.Text("%02d" % (m // (60)),
				12,
				path=path,
				text_anchor="start",
				dominant_baseline="hanging",
				class_="angle",
			))
	
	return g


# Correct for "parallax in altitude"
# which ranges from 54 to 61.5
# and depends on the cosine of the altitude
# the semi diameter of the moon varies from 14.7 to 16.6
# this is a really weird diagram...
def make_lunar_parallax(R):
	g = draw.Group()
	offset = 200
	alt_max = 88
	hp_min = 54.0
	hp_max = 62.0
	hp_range = hp_max - hp_min

	sd_min = 14.7
	sd_max = 16.6

	# the semi diameter of the moon is related to the
	# HP by the factor .2724, so we can add that in here
	def r_func(hp,alt): return offset + (R - offset) * (hp - hp_min) / hp_range
	def a_func(hp,alt): return (cos(radians(alt))) * hp * 6 

	for hp in frange(hp_min, hp_max + 0.01, 0.5):
		pts = []
		for alt in frange(0, alt_max+0.01, 0.1):
			a = a_func(hp,alt)
			r = r_func(hp,alt)
			pts += compute_xy(r, a)

			if modf(hp)[0] == 0 and \
			alt == alt_max and hp != hp_max:
				g.append(draw.Text("%d" % (hp), 12,
					*compute_xy(r,a),
					class_="angle",
				))
		if hp % 5 == 0:
			c = "thick"
		elif hp % 1 == 0:
			c = "thin"
		else:
			c = "extra_thin"

		g.append(draw.Lines(*pts, class_=c))

		if hp % 1:
			continue

		# mark the semi diameters for the differen HP values
		for sd in [ 0.2724 * hp, -0.2724 * hp ]:
			g.append(draw.Lines(
				*compute_xy(R-20, sd * 6),
				*compute_xy(R, sd * 6),
				class_=c
			))
			g.append(draw.Lines(
				*compute_xy(offset-20, sd * 6),
				*compute_xy(offset, sd * 6),
				class_=c
			))


	for alt in [0,2,4,6,7,8,9] + frange(10, alt_max+1, 1):
		pts = []
		for hp in frange(hp_min, hp_max + 0.01, 0.1):
			a = a_func(hp,alt)
			r = r_func(hp,alt)
			pts += compute_xy(r, a)
		if int(alt % 10) == 0:
			c = "extra_thick"
		elif int(alt % 5) == 0:
			c = "thick"
		else:
			c = "thin"
		path = draw.Lines(*pts, class_=c)
		g.append(path)

		if int(alt % 10) != 0 or alt == 0:
			continue
		g.append(draw.Text(("%d") % (alt), 12,
			path=path,
			text_anchor="start",
			class_="angle",
		))
		g.append(draw.Text(("%d") % (alt), 12,
			path=path,
			text_anchor="end",
			class_="angle",
		))

	# draw some thick lines at the semi-diameters
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
def make_pointer(id="pointer"):
	pointer = draw.Group(id=id, class_="spinner")
	pointer.append(draw.Line(0,0, 500, 0, fill="none", stroke="blue", stroke_width=2))
	pointer.append(draw.Line(0,0, -500, 0, fill="none", stroke="none", stroke_width=2))
	return pointer

inner.append(draw_marker("", cut, 180))


# computing the lunar increments
# do we still want this?
#inner.append(make_moon(cut))
#inner.append(make_fractional_minutes(cut-50, side=2, font_sz=10, max_angle=15, include_red=False, include_marker=True, divisions=60))

inner.append(make_lunar_parallax(cut - 30))
inner.append(make_fractional_minutes(cut, side=1, font_sz=10, max_angle=60, include_red=True, include_marker=True, divisions=10))




outer.append(draw.Line(cut, 0, outer_cut, 0, class_="extra_thick"))
outer.append(make_fractional_minutes(outer_cut, side=1, font_sz=10, include_red=True))
outer.append(make_fractional_minutes(cut, side=2, font_sz=10, max_angle=60, include_red=True, include_marker=True))
#outer.append(draw.Circle(0, 0, (outer_cut+cut)/2, class_="thin"))

front.append(outer)
front.append(inner)
front.append(make_pointer("pointer"))

####
#### Reverse side
#### inner disk is the same size as the outer
####
back = draw.Group(transform="translate(1500 500)")

outer = draw.Group(id="back_outer", class_="spinner")
inner = draw.Group(id="back_inner", class_="spinner")
inner.append(axle)
outer.append(axle)
inner.append(draw.Circle(0,0, cut, class_="thick"))
outer.append(draw.Circle(0,0, outer_cut, class_="thick"))


inner_offset = 100
#inner.append(draw.Circle(0, 0, inner_offset, fill="black"))
inner.append(make_lunar_dist(cut - 30))
inner.append(make_fractional_minutes(cut, side=1, max_angle=60, divisions=10, font_sz=10, include_marker=True))
outer.append(make_fractional_minutes(cut, side=2, max_angle=60, divisions=10, font_sz=10, include_red=True, include_marker=True))
outer.append(make_fractional_minutes(outer_cut, side=1, font_sz=10))

#outer.append(make_fractional_ccl(cut+25))
#outer.append(make_fractional_ccl2(cut, outer_cut - cut))

back.append(make_pointer("back_pointer"))
back.append(outer)
back.append(inner)

d.append(front)
d.append(back)
d.save_svg(output_file)

