#!/usr/bin/env python3
# Moon increments and corrections
# Need to compute (14 deg 19 min / hour + d) * min past hour
# v goes from 0 - 18
# 
# 15 deg for the Sun
# 15 deg 2.4 for Aries
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

# log cosine for CCL computatoin
def make_log_cosine(radius, side=2, include_marker=True, division = 1.0, max_angle=60):
	g = draw.Group()

	# 
	steps = 100
	ranges = frange(3*steps,10*steps, steps//2)
	ranges += frange(10*steps, min(16,max_angle)*steps, steps//4)
	ranges += frange(16*steps, min(40,max_angle)*steps, steps//10)
	ranges += frange(40*steps,max_angle*steps, steps//20)
	for i in ranges:
		lc = log(cos(radians(i/steps)))
		whole = int(lc / division)
		frac = -((-lc) % division)
		#(frac,whole) = modf(lc)
		if whole != 0:
			print("uh oh", i, lc, frac, whole)
		a = -frac * 360 / division

		font_sz = None

		if int(i) % (10*steps) == 0 and i > 10*steps:
			font_sz = 20
			c = "extra_thick"
			l = 25
		elif int(i) % (5*steps) == 0:
			font_sz = 15
			c = "extra_thick"
			l = 20
		elif int(i) % (1*steps) == 0:
			if i > 10*steps or i == 8*steps:
				font_sz = 15
			c = "thick"
			l = 20
		elif int(i) % (steps//2) == 0:
			c = "thin"
			l = 20 if i > 16*steps else 10
		elif int(i) % (steps//10) == 0:
			c = "thin"
			l = 12
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
		g.append(draw.Text(
			"%d" % (i // steps),
			font_sz,
			+16 if side & 2 else -16,
			#(font_sz-2) if side & 2 else -2,
			font_sz-2,
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
			#r_major = h / division
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
			r_major = int(h / division) # discrete levels
			#r_major = h / division # continuous spiral
			return offset + (divs - r_major) / divs * (R - offset - spacing)
		def a_func(h):
			r_minor = (h % division) / division
			return r_minor*360

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

	if not log_scale:
		return g

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
# so a multiplication nomograph can be used to 
def make_lunar_dist(R):
	g = draw.Group()
	offset = 200
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

			if m % (60*10) == 0:
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
		label_d = (max_d+min_d)/2
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


inner.append(make_moon(cut))
inner.append(make_fractional_minutes(cut, side=1, font_sz=10, max_angle=60, include_red=True, include_marker=True, divisions=10))
inner.append(make_fractional_minutes(cut-50, side=2, font_sz=10, max_angle=15, include_red=False, include_marker=True, divisions=60))




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

