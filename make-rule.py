#!/usr/bin/env python3
# Generates the slide rule elements using SVG

from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos
import drawsvg as draw

d = draw.Drawing(2000,1000, origin='center')
h_e_radius = 380

def make_ticks(radius, ticks, length, stroke='black', **style):
	g = draw.Group()
	for angle in ticks:
		g.append(draw.Line(
			-length,0,length,0,
			fill='none',
			stroke=stroke,
			transform="rotate(%.3f) translate(%.3f)" % (angle,radius),
			**style,
		))
	return g

def make_labels(radius, step, start, end, fmter, pos=(1,9), text_angle=+90, fill="black", **style):
	g = draw.Group()
	m = start
	while m < end:
		s = fmter(m) #"%.0f" % (m)
		g.append(draw.Text(s, 10, pos[0], pos[1],
			#align="left",
			fill=fill,
			stroke='none',
			transform="rotate(%.3f) translate(%.3f) rotate(%.3f)" % (m,radius,text_angle),
			**style,
		))
		m += step
	return g

def make_tick_labels(radius, labels, size=10, align="right", text_angle=0, pos=(0,0), fill="black", stroke=None, stroke_width=0.3, length=0, **style):
	g = draw.Group()
	length = 10
	for (angle,label) in labels:
		g.append(draw.Text(label, size, pos[0], pos[1],
			align=align,
			fill=fill,
			stroke='none',
			transform="rotate(%.3f) translate(%.3f) rotate(%.3f)" % (angle, radius, text_angle),
			**style,
		))

		if stroke is None:
			continue

		g.append(draw.Line(
			-length,0,length,0,
			fill='none',
			stroke=stroke,
			stroke_width=stroke_width,
			transform="rotate(%.3f) translate(%.3f)" % (angle,radius),
		))
	return g

def deg2sec(m):
	return "%.0f" % (m/6)

def frange(start, end, step):
	n_items = int(ceil((end - start) / step))
	items = []
	for i in range(n_items):
		items.append(start+i*step)
	return items

def make_rule(radius, major, minor1, minor2, minor3=None, fmt=deg2sec, pos=(1,9), start=0, end=360):
	g = draw.Group()
	g.append(draw.Circle(
		0, 0, radius,
		fill='none',
		stroke='black',
		stroke_width=0.1,
	))
	if minor3 is not None:
		g.append(make_ticks(radius, frange(start, end, minor3), 1, stroke_width=0.1))
	g.append(make_ticks(radius, frange(start, end, minor2), 2, stroke_width=0.1))
	g.append(make_ticks(radius, frange(start, end, minor1), 4, stroke_width=0.2))
	g.append(make_ticks(radius, frange(start, end, major),  8, stroke_width=0.4))
	g.append(make_labels(radius, major, start, end, fmt, pos=pos))
	return g


# Height of eye is 1.76 sqrt(H_e) in meters
def height_of_eye(H_e):
	return 1.76 * sqrt(H_e) * -6

def make_height_of_eye(radius):
	g = draw.Group(transform="rotate(60)")
	major = [height_of_eye(H_e) for H_e in frange(0,20.1,1)]
	minor1 = [height_of_eye(H_e) for H_e in frange(0,20,0.5)]
	minor2 = [height_of_eye(H_e) for H_e in frange(0,5,0.1)]
	minor2 += [height_of_eye(H_e) for H_e in frange(5,10,0.25)]

	g.append(make_ticks(radius, minor2, 2, stroke_width=0.1))
	g.append(make_ticks(radius, minor1, 4, stroke_width=0.2))
	g.append(make_ticks(radius, major,  8, stroke_width=0.3))

	labels = [[height_of_eye(h_e), "%.0f" % (h_e)] for h_e in
		[1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17, 20]]

	g.append(make_tick_labels(
		radius,
		labels,
		pos=(-10,+3),
		text_anchor="end",
	))
	g.append(make_tick_labels(
		radius,
		[[0, "Eye"]],
		pos=(-10,+3),
		text_anchor="end",
		stroke="red",
		length=8,
		stroke_width=0.4,
	))
		
	return g



# Refraction for normal conditions (10C 1010hPa)
def refraction(H_a):
	return 1/tan(radians(H_a + 7.31 / (H_a + 4.4))) * -6

# Combined refraction, semidiameter and parallax table
# from https://www.thenauticalalmanac.com/Increments_and_Corrections/Altitude_Correction_Tables.pdf
# There are four arcs to define:
# - Upper/Lower limb of the sun
# - Oct-Mar / Apr-Sep
# The semidiameter for oct-march is 32.3/2 = 16.15
# and for apr-sep 31.8/2 = 15.90
# instead we can have four starting lines and one refraction table
# TODO: add all twelve months, make better symbols
def make_refraction(radius):
	sd_1 = 16.2
	sd_2 = 15.9
	g = draw.Group(transform="rotate(+0)")
	majors = frange(3,20,1) + frange(20,45,5) + frange(50,90.1,10)
	minors1 = frange(3,20,0.5) + frange(20,40,1) + frange(30,90.1,5)
	minors2 = frange(3,10,0.1) + frange(10,20,0.25) + frange(20,40,0.5) + frange(40,60,1) + frange(60,90,2.5)

	g.append(make_ticks(radius, [ refraction(a) for a in majors], 8, stroke_width=0.3))
	g.append(make_ticks(radius, [ refraction(a) for a in minors1], 4, stroke_width=0.2))
	g.append(make_ticks(radius, [ refraction(a) for a in minors2], 2, stroke_width=0.1))
	g.append(make_tick_labels(
		radius,
		[[refraction(a), "%.0f" % (a)] for a in majors],
		size=8.5,
		pos=(-10,+3),
		text_anchor="end",
	))

	labels = [
		[0, "Stars----"],
		[-sd_1*6, "Oct-Mar" ],
		[-sd_2*6, "Apr-Sep\n(Lower)" ],

		[sd_1*6, "Oct-Mar\n(Upper)" ],
		[sd_2*6, "Apr-Sep" ],
	]

	#g.append(make_ticks(radius, [_[0] for _ in labels], 8, stroke="red"))
	g.append(make_tick_labels(radius, labels,
		pos=(-9,2),
		text_anchor="end",
		length=8,
		stroke="red",
	))
	#g.append(make_ticks(radius-30, [sd_1*6], 8, stroke="red"))
	return g

# Parallax table from https://thenauticalalmanac.com/DRIPS.pdf
# what's the formula?
def make_parallax(radius):
	ticks = [
		#[-0.14*60, "0"],
		#[0.13*60, "25"],
		#[0.12*60, "35"],
		[-0.11*60, "40"],
		#[0.10*60, "45"],
		[-0.09*60, "50"],
		#[0.08*60, "55"],
		[-0.07*60, "60"],
		#[0.06*60, "65"],
		[-0.05*60, "70"],
		#[0.04*60, "75"],
		[-0.03*60, "80"],
		#[0.01*60, "85"],
		[-0.00*60, "90"],
	]
	angle = -0.14 * 60 # align with the zero on the height of eye
	g = draw.Group(transform="rotate(%.3f)" % (-angle))
	g.append(make_ticks(radius, [_[0] for _ in ticks], 8, stroke_width=0.3))
	g.append(make_tick_labels(radius, ticks,
		text_anchor="end",
		pos=(-10,+3),
	))
	return g

# Sun semi diameter for upper or lower
# from https://thenauticalalmanac.com/DRIPS.pdf
def make_semidiameter(radius):
	g = draw.Group(transform="rotate(-0)")
	ticks1 = [
		[16.29*6, "Jan"],
		[16.26*6, "Feb"],
		[16.17*6, "Mar"],
		[16.03*6, "Apr"],
		[15.90*6, "May"],
		[15.80*6, "Jun"],
		[15.75*6, "Jul"],
	]
	minor1 = [16.28*6, 16.21*6, 16.10*6, 15.96*6, 15.84*6, 15.77*6]
	ticks2 = [
		[15.78*6, "Aug"],
		[15.87*6, "Sep"],
		[16.00*6, "Oct"],
		[16.14*6, "Nov"],
		[16.24*6, "Dec"],
	]
	minor2 = [15.76*6, 15.82*6, 15.94*6, 16.07*6, 16.20*6, 16.27*6]
	g.append(make_ticks(radius, [0], 8, stroke_width=1, stroke="red"))
	g.append(make_ticks(radius-10, [_[0] for _ in ticks1], 6, stroke_width=0.3))
	g.append(make_ticks(radius-10, minor1, 3, stroke_width=0.2))
	g.append(make_tick_labels(radius, ticks1,
		size=6,
		text_anchor="start",
		pos=(0,+4),
	))
	#g.append(make_ticks(radius-20, [_[0] for _ in ticks2], 6, stroke_width=0.3))
	g.append(make_ticks(radius-20, minor2, 3, stroke_width=0.2))
	g.append(make_tick_labels(radius-20, ticks2,
		size=6,
		text_anchor="end",
		pos=(-10,0),
		stroke="black",
		length=6,
		stroke_width=0.3,
	))
	return g

# This is the scale to adjust the minutes of the declination based on
# the number of minutes past the hour (using the d value from the almanac)
# TODO: handle +/- 12 hours of the day?
# TODO: add lines to help with alignment
def make_d_lines(radius):
	g = draw.Group(transform="rotate(-180)")
	inner_step = 200
	for d in frange(0.1, 1.1, 0.1):
		points = []
		for t in frange(-12, 12.1, 0.1):
			r = radius - inner_step * d
			a = radians(t * d * 6)
			points.append(r*cos(a))
			points.append(r*sin(a))
		g.append(draw.Lines(*points, fill="none", stroke="black", stroke_width=0.1))

	labels = []
	for t in range(0,25):
		labels.append([(t-12)*6+0.7, "%02d:00" % (t)])

	g.append(make_tick_labels(radius - inner_step, labels, size=6, text_anchor="end", pos=(-5,2)))

	labels = []
	for t in range(0,25):
		labels.append([(12-t)*6-0.7, "%02d:00" % (t)])
	g.append(make_tick_labels(radius - inner_step, labels, size=6, text_anchor="end", pos=(-5,2), text_style="italic", fill="red"))

	# quarter hour marks
	for t in frange(-12,12.01,0.25):
		points = []
		for d in frange(0.3, 1.01, 0.1):
			r = radius - inner_step * d
			a = radians(t * d * 6)
			points.append(r*cos(a))
			points.append(r*sin(a))
		g.append(draw.Lines(*points, fill="none", stroke="black", stroke_width=0.1))

	# half hour marks
	for t in frange(-12,12.1,0.5):
		points = []
		for d in frange(0.1, 1.1, 0.1):
			r = radius - inner_step * d
			a = radians(t * d * 6)
			points.append(r*cos(a))
			points.append(r*sin(a))
		g.append(draw.Lines(*points, fill="none", stroke="black", stroke_width=0.2))

	# full hour marks
	for t in frange(-12,12.1,1):
		points = []
		for d in frange(0.1, 1.1, 0.1):
			r = radius - inner_step * d
			a = radians(t * d * 6)
			points.append(r*cos(a))
			points.append(r*sin(a))
		g.append(draw.Lines(*points, fill="none", stroke="black", stroke_width=0.4))

	# and one to help line up on the 12:00
	g.append(draw.Lines(radius, 0, radius-inner_step, 0, stroke="red", stroke_width=0.5));

	return g

# convert gha increment into degrees and minutes
def make_gha_scale(radius):
	g = draw.Group()
	g.append(make_rule(radius, 360/20, 360/(20*6),
		360/(20*12),
		minor3=360/(20*60),
		fmt=lambda x: "%02d:00\n%d\n%d" % (x//18, 20+x//18, 40+x//18),
		pos=(0,-4),
	))

	g.append(make_rule(radius-20, 360/30, 360/(60*5), 360/(60*10),
		fmt=lambda x: "%02d°%02.0f'\n%02d\n%02d" % (x//72, (x % 72) * 30/36, 5+x//72, 10+x//72),
		pos=(1,+12)
	))
	#g.append(make_labels(radius, 4, 0, 360, lambda x: "%.0f" % ((90 - x // 4) % 90), font_style="italic", fill="red", text_anchor="end", pos=(-2,-2)))
	return g

# Sine is one quadrant for increased accuracy
def make_sine(radius):
	g = draw.Group()
	labels = []
	minor1 = []
	minor2 = []
	minor3 = []
	for a in frange(0,0.9,0.05):
		labels.append([degrees(asin(a)*4), "%.2f" % (a)])
	for a in frange(0.90,0.951,0.01):
		labels.append([degrees(asin(a)*4), "%.2f" % (a)])
	for a in frange(0.955,0.99999,0.005):
		labels.append([degrees(asin(a)*4), "%.3f" % (a)])

	for a in frange(0,1.01,0.05):
		minor1.append(degrees(asin(a))*4)
		#minor1.append(180-degrees(asin(a)))
	for a in frange(0,1.01,0.01):
		minor2.append(degrees(asin(a))*4)
		#minor2.append(180-degrees(asin(a)))
	for a in frange(0,1.001,0.005):
		minor3.append(degrees(asin(a))*4)
		#minor2.append(180-degrees(asin(a)))
	for a in frange(0.9,1.0001,0.001):
		minor3.append(degrees(asin(a))*4)

	g.append(draw.Circle(
		0, 0, radius,
		fill='none',
		stroke='black',
		stroke_width=0.1,
	))

	g.append(make_ticks(radius, minor3, 2, stroke_width=0.1))
	g.append(make_ticks(radius, minor2, 4, stroke_width=0.2))
	g.append(make_ticks(radius, minor1, 6, stroke_width=0.4))
	g.append(make_tick_labels(radius, labels,
		text_angle=90,
		pos=(1,9),
		length=8,
		stroke_width=0.4,
		stroke="black",
	))

	# add a fake label for 1.0 at the far end
	g.append(make_tick_labels(radius,
		[[359, "1.00"]],
		text_angle=90,
		pos=(1,9),
		text_anchor="end",
	))
	return g


####
#### Front side
####
# Outer rules for 0-360 degrees with negative markers
front = draw.Group(transform="translate(-500 0)")


outer = draw.Group()
# Minutes
outer.append(make_rule(430, 360/60, 360/120, 360/600))
outer.append(make_labels(430, 6, 0, 360, lambda x: "-%.0f" % ((60-x/6) % 60), pos=(-2,-2), text_anchor="end", fill="red", font_style="italic"))
front.append(outer)

inner = draw.Group()
inner.append(make_rule(400, 360/60, 360/120, 360/600))
# add an reverse scale for the inner ring
inner.append(make_labels(400, 6, 0, 360, lambda x: "-%.0f" % ((60-x/6) % 60), pos=(-2,-2), text_anchor="end", fill="red", font_style="italic"))

inner.append(make_height_of_eye(h_e_radius))

# The refraction, parallax and semi diameter can all be done with
# the one Altitude Correction Table (ACT)
inner.append(make_refraction(h_e_radius))
#d.append(make_parallax(h_e_radius))
#d.append(make_semidiameter(h_e_radius))
#d.append(make_act(h_e_radius)

# sin scale
#d.append(make_sine(500))

inner.append(make_d_lines(405))

front.append(inner)

# Cut lines
front.append(draw.Circle(0,0, 10, fill="none", stroke="black", stroke_width=1))
front.append(draw.Circle(0,0, 415, fill="none", stroke="black", stroke_width=1))
front.append(draw.Circle(0,0, 450, fill="none", stroke="black", stroke_width=1))

pointer = draw.Group()
pointer.append(draw.Line(0,0, 500, 0, fill="none", stroke="blue", stroke_width=2))
pointer.append(draw.Line(0,0, -500, 0, fill="none", stroke="none", stroke_width=2))
front.append(pointer)


####
#### Reverse side (no rotating parts)
####
back = draw.Group(transform="translate(500 0)")
back.append(draw.Circle(0,0, 10, fill="none", stroke="black", stroke_width=1))
back.append(draw.Circle(0,0, 450, fill="none", stroke="black", stroke_width=1))

# rule for 360 degree circle with reverse angles as well
back.append(make_rule(420, 5, 1, 0.5, fmt=lambda x: "%.0f" % (x)))
back.append(make_labels(420, 5, 0, 360, lambda x: "-%.0f" % ((360-x) % 360), pos=(-2,-2), text_anchor="end", fill="red", font_style="italic"))

# 24-hour clock
back.append(make_rule(440, 360/(24*2), 360/(24*4), 360/(24*60), fmt=lambda x: "%02d:%02d" % ((x // 15), (4 * (x % 15)))))

# 90 degree circle and sine/cosine tables
back.append(make_rule(390, 4, 1, 0.5, fmt=lambda x: "%.0f" % (x // 4)))
back.append(make_labels(390, 4, 0, 360, lambda x: "%.0f" % ((90 - x // 4) % 90), font_style="italic", fill="red", text_anchor="end", pos=(-2,-2)))
back.append(make_sine(370))

back.append(make_gha_scale(340))


d.append(front)
d.append(back)
d.save_svg('rule.svg')

