#!/usr/bin/env python3
# Generates the slide rule elements using SVG

from math import sqrt, sin, cos, atan2, ceil
import drawsvg as draw

d = draw.Drawing(1000,1000, origin='center')

def make_ticks(radius, ticks, length, **style):
	g = draw.Group()
	for angle in ticks:
		g.append(draw.Line(
			-length,0,length,0,
			fill='none',
			stroke='black',
			transform="rotate(%.3f) translate(%.3f)" % (angle,radius),
			**style,
		))
	return g

def make_labels(radius, step, start, end, fmter, text_angle=+90, **style):
	g = draw.Group()
	m = start
	while m < end:
		s = fmter(m) #"%.0f" % (m)
		g.append(draw.Text(s, 10, 1, +9,
			align="left",
			fill='black',
			stroke='none',
			transform="rotate(%.3f) translate(%.3f) rotate(%.3f)" % (m,radius,text_angle),
			*style,
		))
		m += step
	return g

def make_tick_labels(radius, labels, size=10, align="right", pos=(0,0), **style):
	g = draw.Group()
	length = 10
	thick = 0.2
	text_angle = 0
	for (angle,label) in labels:
		g.append(draw.Text(label, size, pos[0], pos[1],
			align=align,
			fill='black',
			stroke='none',
			transform="rotate(%.3f) translate(%.3f) rotate(%.3f)" % (angle, radius, text_angle),
			**style,
		))
#		g.append(draw.Line(
#			-length,0,length,0,
#			fill='none',
#			stroke='black',
#			stroke_width=thick,
#			transform="rotate(%.3f) translate(%.3f)" % (angle,radius),
#		))
	return g

def deg2sec(m):
	return "%.0f" % (m/6)

def frange(start, end, step):
	n_items = int(ceil((end - start) / step))
	return (start + i*step for i in range(n_items))

def make_rule(radius, major, minor1, minor2, start=0, end=360):
	g = draw.Group()
	g.append(draw.Circle(
		0, 0, radius,
		fill='none',
		stroke='black',
		stroke_width=0.1,
	))
	g.append(make_ticks(radius, frange(start, end, minor2), 2, stroke_width=0.1))
	g.append(make_ticks(radius, frange(start, end, minor1), 4, stroke_width=0.2))
	g.append(make_ticks(radius, frange(start, end, major),  8, stroke_width=0.4))
	g.append(make_labels(radius, major, start, end, deg2sec))
	return g


# Height of eye is 1.76 sqrt(H_e) in meters
def height_of_eye(H_e):
	return 1.76 * sqrt(H_e) * -6

def make_height_of_eye(h_e_radius = 370):
	h_e_major = [height_of_eye(H_e) for H_e in frange(0,20.1,1)]
	h_e_minor1 = [height_of_eye(H_e) for H_e in frange(0,20,0.5)]
	h_e_minor2 = [height_of_eye(H_e) for H_e in frange(0,5,0.1)]
	h_e_minor2 += [height_of_eye(H_e) for H_e in frange(5,10,0.25)]

	g = draw.Group()
	g.append(make_ticks(h_e_radius, h_e_minor2, 2, stroke_width=0.1))
	g.append(make_ticks(h_e_radius, h_e_minor1, 4, stroke_width=0.2))
	g.append(make_ticks(h_e_radius, h_e_major,  8, stroke_width=0.3))

	h_e_labels = [[height_of_eye(h_e), "%.0f" % (h_e)] for h_e in
		[0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17, 20]]
	g.append(make_tick_labels(h_e_radius, h_e_labels, pos=(-10,+3), stroke_width=0.3, text_anchor="end"))
	return g

d.append(make_height_of_eye())


# Refraction for normal conditions
def refraction(H_a):
	return cot(H_a + 7.31 / (H_a + 4.4))

#height_of_eye_major = [[1.76 * sqrt(H_e) * -6, "%.1f" % (H_e)] for H_e in [0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 18, 22]]
#d.append(make_tick_labels(350, height_of_eye))

d.append(make_rule(430, 360/60, 360/120, 360/600))
d.append(make_rule(400, 360/60, 360/120, 360/600))

d.save_svg('rule.svg')

