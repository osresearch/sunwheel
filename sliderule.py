#!/usr/bin/env python3
# Circular slide rule utility functions (using drawsvg)
from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan, floor, fabs, modf
import drawsvg as draw
from almanac import haversine, ahaversine, frange, refraction, equation_of_time, julian, declination, declination_perp, compute_xy, height_of_eye, horizon_distance, stereographic_project

deg_symbol = "°"
right_arrow = "➤"
right_arrow3 = right_arrow+right_arrow+right_arrow
left_arrow = "⮜"
left_arrow3 = left_arrow+left_arrow+left_arrow

css = """
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
	font-family: "B612 Italic";
}
"""

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
def make_fractional_minutes(
	radius,
	include_marker=False,
	side=1,
	max_angle=100,
	offset = 0,
	font_sz = 10,
	include_red=False,
	divisions=10,
):
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



# translation happens in the old reference frame
def append(d, g, x, y, s):
	g2 = draw.Group(transform="scale(%.3f %.3f) translate(%.3f %.3f)" % (s, s, x, y))
	g2.append(g)
	d.append(g2)
	return d

# Pointer with hidden half so it spins around the center
def make_pointer(id="pointer"):
	pointer = draw.Group(id=id, class_="spinner", transform="rotate(0)")
	pointer.append(draw.Line(0,0, 500, 0, fill="none", stroke="blue", stroke_width=2))
	pointer.append(draw.Line(0,0, -500, 0, fill="none", stroke="none", stroke_width=2))
	return pointer

def draw_axle():
	return draw.Circle(0,0, 5, class_="thick")

def draw_a3():
	a3 = draw.Drawing("420mm", "297mm", origin=(0,0))
	a3.append_css(css)
	return a3

def draw_a4():
	a4 = draw.Drawing("297mm", "210mm", origin=(0,0))
	a4.append_css(css)
	return a4

def append_a3(a3,
	outer_cut,
	inner_cut,
	out1,
	in1,
	out2,
	in2,
	dpi = 96,
	outer_diameter = 170,
	margin = 10,
):
	a3_scaling = outer_diameter / 1000 * dpi / 25.4
	a3_width = (420 * dpi / 25.4) / a3_scaling
	a3_height = (297 * dpi / 25.4) / a3_scaling

	# inner is slightly smaller, so tweak its position to just fit
	mid_h = a3_height - outer_cut - inner_cut - 2 * margin
	d1 = sqrt((outer_cut + inner_cut + margin)**2 - mid_h**2)

	append(a3, out1, outer_cut+margin, outer_cut+margin, a3_scaling)
	append(a3, in1, outer_cut+margin+d1, a3_height - inner_cut - margin, a3_scaling)
	append(a3, out2, a3_width - margin - outer_cut, a3_height - margin - outer_cut, a3_scaling)
	append(a3, in2, a3_width - margin - outer_cut - d1, inner_cut + margin, a3_scaling)

def append_a4(pages,
	outer_cut,
	inner_cut,
	out1,
	in1,
	out2,
	in2,
	dpi = 96,
	outer_diameter = 170,
	margin = 10,
):
	a4_scaling = outer_diameter / 1000 * dpi / 25.4
	a4_width = (297 * dpi / 25.4) / a4_scaling
	a4_height = (210 * dpi / 25.4) / a4_scaling

	# inner is slightly smaller, so tweak its position to just fit
	mid_h = a4_height - outer_cut - inner_cut - 2 * margin
	d1 = sqrt((outer_cut + inner_cut + margin)**2 - mid_h**2)

	append(pages[0], out1, outer_cut+margin, a4_height/2, a4_scaling)
	append(pages[1], out2, outer_cut+margin, a4_height/2, a4_scaling)
	append(pages[2], in1, inner_cut+margin, inner_cut+margin, a4_scaling)
	append(pages[2], in2, a4_width -(inner_cut+margin), a4_height-(inner_cut+margin), a4_scaling)
