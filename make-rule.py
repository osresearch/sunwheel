#!/usr/bin/env python3
# Generates the slide rule elements using SVG

from math import sqrt, sin, cos, tan, atan2, ceil, radians
import drawsvg as draw

d = draw.Drawing(1000,1000, origin='center')
h_e_radius = 370

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
	items = []
	for i in range(n_items):
		items.append(start+i*step)
	return items

def make_rule(radius, major, minor1, minor2, fmt=deg2sec, start=0, end=360):
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
	g.append(make_labels(radius, major, start, end, fmt))
	return g


# Height of eye is 1.76 sqrt(H_e) in meters
def height_of_eye(H_e):
	return 1.76 * sqrt(H_e) * -6

def make_height_of_eye(radius):
	major = [height_of_eye(H_e) for H_e in frange(0,20.1,1)]
	minor1 = [height_of_eye(H_e) for H_e in frange(0,20,0.5)]
	minor2 = [height_of_eye(H_e) for H_e in frange(0,5,0.1)]
	minor2 += [height_of_eye(H_e) for H_e in frange(5,10,0.25)]

	g = draw.Group()
	g.append(make_ticks(radius, minor2, 2, stroke_width=0.1))
	g.append(make_ticks(radius, minor1, 4, stroke_width=0.2))
	g.append(make_ticks(radius, major,  8, stroke_width=0.3))

	labels = [[height_of_eye(h_e), "%.0f" % (h_e)] for h_e in
		[0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17, 20]]
	g.append(make_tick_labels(
		radius,
		labels,
		pos=(-10,+3),
		stroke_width=0.3,
		text_anchor="end"),
	)
	return g

d.append(make_height_of_eye(h_e_radius))


# Refraction for normal conditions (10C 1010hPa)
def refraction(H_a):
	return 1/tan(radians(H_a + 7.31 / (H_a + 4.4))) * -6

def make_refraction(radius):
	g = draw.Group(transform="rotate(-60)")
	majors = frange(5,20,1) + frange(20,45,5) + frange(50,90.1,10)
	minors1 = frange(5,20,0.5) + frange(20,40,1) + frange(30,90.1,5)
	minors2 = frange(5,10,0.1) + frange(10,20,0.25) + frange(20,40,0.5) + frange(40,60,1) + frange(60,90,2.5)

	g.append(make_ticks(radius, [refraction(a) for a in majors], 8, stroke_width=0.3))
	g.append(make_ticks(radius, [refraction(a) for a in minors1], 4, stroke_width=0.2))
	g.append(make_ticks(radius, [refraction(a) for a in minors2], 2, stroke_width=0.1))
	g.append(make_tick_labels(
		radius,
		[[refraction(a), "%.0f" % (a)] for a in majors],
		size=8.5,
		pos=(-10,+3),
		text_anchor="end",
	))
	return g

d.append(make_refraction(h_e_radius))


# Outer rules for 0-360 degrees and 24-hour clock
d.append(make_rule(460, 5, 1, 0.5, fmt=lambda x: "%.0f" % (x)))
d.append(make_rule(480, 360/(24*2), 360/(24*4), 360/(24*60), fmt=lambda x: "%02d:%02d" % ((x // 15), (4 * (x % 15)))))

d.append(make_rule(440, 360/60, 360/120, 360/600))
d.append(make_rule(400, 360/60, 360/120, 360/600))

d.save_svg('rule.svg')

