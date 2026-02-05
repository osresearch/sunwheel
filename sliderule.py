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

dpi = 96
a3_width = 420 * dpi / 25.4
a3_height = 297 * dpi / 25.4

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
text {
	font-family: "B612 Regular";
	pointer-events: none;
}
.italic {
	font-family: "B612 Italic";
	pointer-events: none;
}

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
.red_thick {
	fill: none;
	stroke: red;
	stroke-width: 1;
}
.thin {
	fill: none;
	stroke: black;
	stroke-width: 0.5;
}
.extra_thin {
	fill: none;
	stroke: #666;
	stroke-width: 0.4;
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

	for i in range(1 if include_marker else 0,int(max_angle*divisions)):
		a = 360 * i / (max_angle*divisions)
		sz = None
		ta = None
		txt = "%d" % (i // divisions)

		if i % (10*divisions) == 0:
			sz = font_sz + 2
			c = "extra_thick"
			l = 25
			ta = 0 #90
		elif i % divisions == 0:
			sz = font_sz
			ta = 0
			c = "thick"
			l = 20
		elif divisions == 40 and i % (divisions // 2) == 0:
			c = "thick" if divisions == 40 else "thin" 
			l = 15
			sz = font_sz - 2
			txt = "%.1f" % (i / divisions)
			ta = 0
		elif i % (divisions//2) == 0:
			c = "thin" 
			l = 15
		elif divisions == 40 and i % (divisions // 10) == 0:
			c = "thin"
			l = 12
		elif divisions == 40 and i % (divisions // 20) == 0:
			c = "thin"
			l = 8
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

		if ta == 90:
			xp1 = 1
			yp1 = sz+10 if side & 1 else -10
			xp2 = -1
			yp2 = sz+10 if side & 1 else -10
		else:
			xp1 = -20 if side & 1 else +5
			yp1 = sz
			xp2 = xp1
			yp2 = -2
		g.append(draw.Text(
			txt,
			sz,
			#+12 if side & 2 else -12,
			#(sz-1),
			xp1,
			yp1,
			class_="angle",
			#text_anchor="start" if side & 2 else "start",
			text_anchor="start", # if ta == 90 else "end",
			transform="rotate(%.3f) translate(%.3f 0) rotate(%d)" % (a,radius, ta),
		))

		if not include_red:
			continue
		g.append(draw.Text(
			txt,
			sz,
			#+12 if side & 2 else -12,
			#(font_sz-2) if side & 2 else -2,
			#-2,
			xp2,
			yp2,
			class_="red_angle",
			text_anchor="start" if ta != 90 else "end",
			transform="rotate(%.3f) translate(%.3f 0) rotate(%d)" % (-a,radius, ta),
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
	pointer.append(draw.Lines(
		0,0,
		0,-40,
		500, -20,
		500, +20,
		0,+40,
		0,0,
		fill="#ffffff01",
		stroke="#00008080",
		stroke_width=1,
	))
	pointer.append(draw.Line(0,0, 500, 0, fill="none", stroke="blue", stroke_width=2))
	pointer.append(draw.Line(500,0, -500, 0, fill="none", stroke="none", stroke_width=10))
	pointer.append(draw.Circle(0,0, 500, fill="none", stroke="#ffffff01", stroke_width=1))
	pointer.append(draw.Circle(0,0, 40, fill="#ffffff01", stroke="blue", stroke_width=1, class_="recenter", id_=id+"_recenter"));
	return pointer

def draw_axle():
	return draw.Circle(0,0, 5, class_="thick")

def draw_a3():
	a3 = draw.Drawing("420mm", "297mm", origin=(0,0))
	a3.append_css(css)
	return a3

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
	a3_scaled_width = a3_width / a3_scaling
	a3_scaled_height = a3_height / a3_scaling

	# inner is slightly smaller, so tweak its position to just fit
	mid_h = a3_scaled_height - outer_cut - inner_cut - 2 * margin
	d1 = sqrt((outer_cut + inner_cut + margin)**2 - mid_h**2)

	append(a3, out1, outer_cut+margin, outer_cut+margin, a3_scaling)
	append(a3, in1, outer_cut+margin+d1, a3_scaled_height - inner_cut - margin, a3_scaling)
	append(a3, out2, a3_scaled_width - margin - outer_cut, a3_scaled_height - margin - outer_cut, a3_scaling)
	append(a3, in2, a3_scaled_width - margin - outer_cut - d1, inner_cut + margin, a3_scaling)


def append_dragging(d):
	d.append_javascript("""
var dragging = false;
var drag_target = null;
var drag_cx;
var drag_cy;
var drag_angle_start = null;
function drag_init(ev) {
	var svg = ev.target;
	dragging = false;
	for(el of svg.getElementsByClassName("spinner"))
	{
		console.log(el);
		el.angle = 0
		el.addEventListener('mousedown', drag_start);
		el.addEventListener('mousemove', drag)
		el.addEventListener('mouseup', drag_end);

		el.addEventListener('touchstart', drag_start);
		el.addEventListener('touchmove', drag)
		el.addEventListener('touchend', drag_end);
		el.addEventListener('touchcancel', drag_end);
	}

	for(el of svg.getElementsByClassName("recenter"))
	{
		el.addEventListener('mousedown', recenter);
	}
}
function rotate(el, angle)
{
	el.angle = angle;
	el.style.transform = "rotate(" + el.angle.toFixed(3) + "deg)";
}
function recenter(evt)
{
	console.log("recenter", evt.target);
	var prefix = evt.target.id.startsWith("back_") ? "back_" : "";
		
	var pointer = document.getElementById(prefix+"pointer");
	var inner = document.getElementById(prefix+"inner");
	var outer = document.getElementById(prefix+"outer");

	rotate(inner, inner.angle - pointer.angle);
	rotate(outer, outer.angle - pointer.angle);
	rotate(pointer, 0);

}
function drag_start(evt)
{
	// find the parent that is the spinner
	drag_target = evt.target
	while(drag_target && !drag_target.classList.contains("spinner"))
	{
		drag_target = drag_target.parentElement;
	}
	if (!drag_target)
		return;
	dragging = true;

	var rect = drag_target.getClientRects()[0];
	drag_cx = rect.x + rect.width/2;
	drag_cy = rect.y + rect.height/2;
	if (!drag_target.angle)
		drag_target.angle = 0;
	drag_angle_start = null;
	console.log("drag start", evt, drag_target, drag_cx, drag_cy);
	drag_target.classList.remove("spinner")
}
function drag_end(evt)
{
	if (drag_target)
	{
		drag_target.classList.add("spinner")
		drag_target = null;
	}

	if (!dragging)
		return

	console.log("drag end", evt);
	dragging = false;
}
function drag(evt)
{
	if (!dragging || !drag_target)
		return;
	if(evt.preventDefault)
		evt.preventDefault();

	if (evt.buttons == 0)
	{
		// we have somehow lost the button; maybe the mouse left the window
		// was released and then came back in
		return drag_end(evt);
	}

	var x = evt.touches ? evt.touches[0].clientX : evt.clientX;
	var y = evt.touches ? evt.touches[0].clientY : evt.clientY;
	var a = Math.atan2(y - drag_cy, x - drag_cx) * 180 / Math.PI;
	if (drag_angle_start == null)
		drag_angle_start = a;
	var da = a - drag_angle_start;
	//console.log("drag", evt, evt.layerX, evt.layerY, a, drag_a, a - drag_a);
	if (da < -180)
		da += 360;
	if (da > +180)
		da -= 360;
	drag_angle_start = a;
	rotate(drag_target, drag_target.angle + da);
}
""")
