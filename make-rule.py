#!/usr/bin/env python3
# Generates the slide rule elements using SVG

from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan
import drawsvg as draw

d = draw.Drawing(2000,1000, origin='center')
h_e_radius = 380

def make_ticks(radius, ticks, length, log_scale=None, stroke='black', **style):
	g = draw.Group()
	for angle in ticks:
		if log_scale:
			angle = log(angle) * 360 / log_scale
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

def make_tick_labels(radius, labels, size=10, log_scale=None, align="right", text_angle=0, pos=(0,0), fill="black", stroke=None, stroke_width=0.3, length=0, **style):
	g = draw.Group()
	for (angle,label) in labels:
		if log_scale:
			angle = log(angle) * 360 / log_scale
		g.append(draw.Text(label, size, pos[0], pos[1],
			align=align,
			fill=fill,
			stroke='none',
			transform="rotate(%.3f) translate(%.3f) rotate(%.3f)" % (angle, radius, text_angle),
			**style,
		))

		if length <= 0:
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

def frange(start, end, step=1):
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
		g.append(make_ticks(radius, frange(start, end, minor3), 2, stroke_width=0.1))
	g.append(make_ticks(radius, frange(start, end, minor2), 3, stroke_width=0.1))
	g.append(make_ticks(radius, frange(start, end, minor1), 5, stroke_width=0.2))
	g.append(make_ticks(radius, frange(start, end, major),  8, stroke_width=0.4))
	g.append(make_labels(radius, major, start, end, fmt, pos=pos))
	return g


# Height of eye is 1.76 sqrt(H_e) in meters
def height_of_eye(H_e):
	return 1.76 * sqrt(H_e) * -6

def make_height_of_eye(radius):
	g = draw.Group(transform="rotate(-120)")
	major = [height_of_eye(H_e) for H_e in frange(0,20.1,1)]
	minor1 = [height_of_eye(H_e) for H_e in frange(0,20,0.5)]
	minor2 = [height_of_eye(H_e) for H_e in frange(0,5,0.1)]
	minor2 += [height_of_eye(H_e) for H_e in frange(5,10,0.25)]

	g.append(make_ticks(radius-10, minor2, 4, stroke_width=0.1))
	g.append(make_ticks(radius-10, minor1, 8, stroke_width=0.2))
	g.append(make_ticks(radius-10, major,  15, stroke_width=0.3))

	labels = [[height_of_eye(h_e), "%.0f" % (h_e)] for h_e in
		[1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17, 20]]

	g.append(make_tick_labels(
		radius-10,
		labels,
		pos=(-10,+3),
		text_anchor="end",
	))
	g.append(make_tick_labels(
		radius-10,
		[[0, "Eye"]],
		pos=(-10,+3),
		text_anchor="end",
		stroke="red",
		length=8,
		stroke_width=0.4,
	))
		
	return g


def make_arcs(pts, func, fill="none", stroke="black", stroke_width=1, **style):
	points = []
	for t in pts:
		(r,a) = func(t)
		points.append(r*cos(radians(a)))
		points.append(r*sin(radians(a)))
	return draw.Lines(*points, fill=fill, stroke=stroke, stroke_width=stroke_width, **style)

# Refraction for normal conditions (10C 1010hPa)
# R = (n_air - 1) cot(theta)
# adjustment for non standard presure and temperature
def refraction(H_a, p=1010, t=10):
	r = 1/tan(radians(H_a + 7.31 / (H_a + 4.4)))
	f = p / (273+t) * 283/1010
	return f * r * -6

# Combined refraction, semidiameter and parallax table
# from https://www.thenauticalalmanac.com/Increments_and_Corrections/Altitude_Correction_Tables.pdf
# There are four arcs to define:
# - Upper/Lower limb of the sun
# - Oct-Mar / Apr-Sep
# The semidiameter for oct-march is 32.3/2 = 16.15
# and for apr-sep 31.8/2 = 15.90
# instead we can have four starting lines and one refraction table
# TODO:  make better symbols
def make_refraction(radius):
	sd_1 = 16.2
	sd_2 = 15.9
	g = draw.Group(transform="rotate(-180)")
	majors = frange(3,20,1) + frange(20,45,5) + frange(50,90.1,10)
	minors1 = frange(3,20,0.5) + frange(20,40,1) + frange(30,90.1,5)
	minors2 = frange(3,10,0.1) + frange(10,20,0.25) + frange(20,40,0.5) + frange(40,60,1) + frange(60,90,2.5)

	t_scale = lambda t: radius - 60 - t * 5

	for h_a in majors:
		g.append(make_arcs(frange(-10,30.1,1), lambda t: (t_scale(t), refraction(h_a,1010,t)), stroke_width=0.4))
	for h_a in minors1:
		g.append(make_arcs(frange(-10,30.1,1), lambda t: (t_scale(t), refraction(h_a,1010,t)), stroke_width=0.2))
	for h_a in minors2:
		g.append(make_arcs(frange(-10,30.1,1), lambda t: (t_scale(t), refraction(h_a,1010,t)), stroke_width=0.1))

	for t in [-10,-5,0,5,10,15,20,25,30]:
		r = t_scale(t)
		g.append(make_arcs(minors2,
			lambda a: (r, refraction(a,1010,t)),
			stroke_width= 0.8 if (t % 10 == 0) else 0.1,
		))

		if t % 10 != 0:
			continue
		g.append(draw.Text("%d°C" % (t),
			8.5, -8, -2,
			transform="rotate(%f) translate(%f)" % (refraction(3,1010,t), r),
			text_anchor="center",
		))
		g.append(draw.Text("%d°C" % (t),
			8.5, -8, +10,
			transform="translate(%f)" % (r),
			text_anchor="center",
		))

	g.append(make_tick_labels(
		radius,
		[[refraction(a,1010,0), "%.0f" % (a)] for a in majors],
		size=8.5,
		pos=(-5,+3),
		text_anchor="start",
	))

	labels = [
		[0, "Stars----"],
		[-sd_1*6, "Oct-Mar" ],
		[-sd_2*6, "Apr-Sep\n(Lower)" ],

		[sd_1*6, "Oct-Mar\n(Upper)" ],
		[sd_2*6, "Apr-Sep" ],
	]

	g.append(make_tick_labels(
		radius-25,
		[
			[+sd_1*6-4, "Upper"],
			[-sd_1*6-2, "Lower"],
		],
		text_anchor="center",
		size=8,
	))
	#g.append(make_ticks(radius, [_[0] for _ in labels], 8, stroke="red"))
#	g.append(make_tick_labels(radius, labels,
#		pos=(-9,2),
#		text_anchor="end",
#		length=8,
#		stroke="red",
#	))
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
	g = draw.Group(transform="rotate(-180)")
	ticks1 = [
		[16.29*6, "Jan"],
		[16.26*6, ""],
		[16.17*6, ""],
		[16.03*6, "Apr"],
		[15.90*6, ""],
		[15.80*6, ""],
		[15.75*6, "Jul"],
	]
	minor1 = [16.28*6, 16.21*6, 16.10*6, 15.96*6, 15.84*6, 15.77*6]
	ticks2 = [
		[15.78*6, "Aug"],
		[15.87*6, ""],
		[16.00*6, "Oct"],
		[16.14*6, ""],
		[16.24*6, "Dec"],
	]
	minor2 = [15.76*6, 15.82*6, 15.94*6, 16.07*6, 16.20*6, 16.27*6]
	#g.append(make_ticks(radius, [0], 8, stroke_width=1, stroke="red"))

	for scale in [1,-1]:
		ticks1 = [[_[0]*scale, _[1]] for _ in ticks1]
		ticks2 = [[_[0]*scale, _[1]] for _ in ticks2]
		minor1 = [_*scale for _ in minor1]
		minor2 = [_*scale for _ in minor2]

		g.append(make_ticks(radius-10, [_[0] for _ in ticks1], 5, stroke_width=0.3))
		g.append(make_ticks(radius-10, minor1, 3, stroke_width=0.2))
		g.append(make_tick_labels(radius, ticks1,
			size=6,
			text_anchor="start",
			pos=(-2,+2),
		))

		g.append(make_ticks(radius-25, [_[0] for _ in ticks2], 5, stroke_width=0.3))
		g.append(make_ticks(radius-25, minor2, 3, stroke_width=0.2))
		g.append(make_tick_labels(radius-20, ticks2,
			size=6,
			text_anchor="end",
			pos=(-12,0),
			#stroke="black",
			#length=3,
			#stroke_width=0.3,
		))
	return g

# This is the scale to adjust the minutes of the declination based on
# the number of minutes past the hour (using the d value from the almanac)
# TODO: handle +/- 12 hours of the day?
# TODO: add lines to help with alignment
def make_d_lines(outer_radius):
	g = draw.Group(transform="rotate(+0)")
	inner_step = 320

	radius = lambda d: outer_radius - inner_step * (1-d)

	# horizontal lines for the different values of d
	for d in frange(0.1, 1.1, 0.1):
		r = radius(d)
		g.append(make_arcs(frange(-12, 12.01, 0.1), lambda t: (r, t*d*6), stroke_width=0.1))

		if d > 0.9:
			continue

		ta = radians(6.0 * d * 6)
		tx = r * cos(ta)
		ty = r * sin(ta)

		# mark for the scales, following the 6 lines
		g.append(draw.Text("%.0f" % (d*10), 10, 0, -2,
			fill="black",
			stroke="none",
			text_anchor="end",
			transform="translate(%.3f %.3f) rotate(-90)" % (tx,ty),
		))
		g.append(draw.Text("%.0f" % (d*10), 10, 0, -2,
			fill="black",
			stroke="none",
			text_anchor="start",
			transform="translate(%.3f %.3f) rotate(-90)" % (tx,-ty),
		))

	# quarter hour marks (only half way in)
	for t in frange(-12,12.01,0.25):
		g.append(make_arcs(frange(0.5, 1.01, 0.01),
			lambda d: (radius(d), t*d*6),
			stroke_width=0.1))

	# half hour marks (almost all the way in)
	for t in frange(-12,12.1,0.5):
		g.append(make_arcs(frange(0.2, 1.01, 0.01),
			lambda d: (radius(d), t*d*6),
			stroke_width=0.2))

	# full hour marks
	for t in frange(-12,12.1,1):
		if t == -6 or t == 6 or t == 0:
			stroke = "red"
			width = 1
		else:
			stroke = "black"
			width = 0.5
		g.append(make_arcs(frange(0.1, 1.01, 0.01), lambda d: (radius(d), t*d*6), stroke=stroke, stroke_width=width))

		if t == -12 or t == +12:
			continue
		d = 0.95
		tr = radius(d)
		ta = radians(t * d * 6)
		tx = tr * cos(ta)
		ty = tr * sin(ta)
		ta = degrees(ta) * 1.8
		g.append(draw.Text("%02d:00" % (t + 12), 8, 0, -2,
			text_anchor="middle",
			fill="black",
			transform="translate(%.3f %3.f) rotate(%.3f)" % (tx,ty,ta),
		))
		g.append(draw.Text("%02d:00" % (12 - t), 8, 0, +7,
			text_anchor="middle",
			fill="red",
			font_style="italic",
			transform="translate(%.3f %3.f) rotate(%.3f)" % (tx,ty,ta),
		))

	#g.append(draw.Lines(radius, 0, radius-inner_step, 0, stroke="red", stroke_width=0.5));

	return g

# convert gha increment into degrees and minutes
# This is equvilant to https://www.thenauticalalmanac.com/Increments_and_Corrections/Increments_and_Corrections_Sun_only.pdf
def make_gha_scale(radius):
	g = draw.Group()
	g.append(make_rule(radius,
		360/20,		# 20 minutes around the circle
		360/(20*2),	# every 30 seconds per minute
		360/(20*6),	# every 10 seconds
		minor3=360/(20*60), # every second
		fmt=lambda x: "%02d:00\n%d / %d" % (x//18, 20+x//18, 40+x//18),
		pos=(1,-2),
	))

	g.append(make_rule(radius-15,
		360/(5*4),		# 5 degrees around, marks every 15 seconds 
		360/(5*4*3),		# subdivide into 5/10/15 seconds
		360/(5*4*15),		# every second
		minor3=360/(5*4*15*2),	# every half second
		fmt=lambda x: "%02d°%02.0f'\n%02d° / %02d°" % (x//72, (x % 72) * 30/36, 5+x//72, 10+x//72),
		pos=(1,+12)
	))
	#g.append(make_labels(radius, 4, 0, 360, lambda x: "%.0f" % ((90 - x // 4) % 90), font_style="italic", fill="red", text_anchor="end", pos=(-2,-2)))
	return g

# tangent goes off to infinity as it approaches 90
# cotangent uses the red reverse scale since cot(theta) = tan(90-theta)
def make_tangent_scale(radius):
	g = draw.Group()

	major = []
	minor1 = []
	minor2 = []
	for a in frange(0, 2, 0.1):
		major += [[degrees(atan(a))*4, "%.1f" % (a)]]
	for a in frange(2, 10, 1) + frange(10,18,2) + [20,30,50,90]:
		major += [[degrees(atan(a))*4, "%.0f" % (a)]]

	for a in frange(2, 10, 0.5) + frange(10,30,1):
		minor1 += [degrees(atan(a))*4]
	for a in frange(0, 2, 0.01) + frange(2,5, 0.1) + frange(5, 10, 0.25) + frange(30,90,5):
		minor2 += [degrees(atan(a))*4]

	g.append(make_ticks(radius,
		minor2,
		length=2,
		stroke_width=0.2,
	))
	g.append(make_ticks(radius,
		minor1,
		length=5,
		stroke_width=0.2,
	))
	g.append(make_tick_labels(radius,
		major,
		10,
		text_angle=90,
		pos=(2,8),
		stroke="black",
		length=8,
		stroke_width=0.4,
	))
	g.append(draw.Circle(
		0, 0, radius,
		fill='none',
		stroke='black',
		stroke_width=0.1,
	))

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

	# add a fake label for 1.0 at the far end and some for special values
	g.append(make_tick_labels(radius,
		[[359, "1.00"]],
		text_angle=90,
		pos=(1,9),
		text_anchor="end",
	))

	# and some known values
	g.append(make_tick_labels(radius+5,
		[[30*4, "1/2"], [60*4, "√3/2"], [45*4,"√2/2"]],
		text_angle=90,
		pos=(0,2),
		text_anchor="middle",
		length=1,
		stroke_width=0.2,
		stroke="black",
	))

	return g

def make_sqrt_scale(radius):
	g = draw.Group()

	g.append(draw.Circle(
		0, 0, radius,
		fill='none',
		stroke='black',
		stroke_width=0.1,
	))
	g.append(draw.Circle(
		0, 0, radius-20,
		fill='none',
		stroke='black',
		stroke_width=0.1,
	))
	major = frange(1,10)
	minor1 = frange(1,10,0.5)
	minor2 = frange(1,10,0.1)
	minor3 = frange(1,10,0.05)
	minor4 = frange(1,2, 0.01)

	# the sqrt scale goes up to 10

	g.append(make_ticks(radius-20,
		minor4,
		log_scale=log(10),
		length=2,
		stroke_width=0.1,
		stroke="black",
	))
	g.append(make_ticks(radius-20,
		minor3,
		log_scale=log(10),
		length=4,
		stroke_width=0.1,
		stroke="black",
	))
	g.append(make_ticks(radius-20,
		minor2,
		log_scale=log(10),
		length=6,
		stroke_width=0.2,
		stroke="black",
	))
	g.append(make_ticks(radius-20,
		minor1,
		log_scale=log(10),
		length=8,
		stroke_width=0.2,
		stroke="black",
	))
	g.append(make_tick_labels(radius-20,
		[[_, "%d" % (_)] for _ in major],
		10,
		log_scale=log(10),
		length=10,
		stroke_width=0.4,
		stroke="black",
		text_angle=90,
		pos=(2,-2),
	))

	extra_labels = [[_/10, "%.1f" % (_/10)] for _ in frange(11,20) + [25,35]]
	extra_labels += [[pi, "π"]]
	extra_labels += [[e, "e"]]
	g.append(make_tick_labels(radius-20,
		extra_labels,
		8,
		log_scale=log(10),
		text_angle=90,
		pos=(2,-2),
	))

	# double the scales to go up to 100 for the outside
	major = major + [10 * _ for _ in major]
	minor1 = minor1 + [10 * _ for _ in minor1]
	minor2 = minor2 + [10 * _ for _ in minor2]
	minor3 = minor3 + [10 * _ for _ in minor3]
	minor4 = minor4 + [10 * _ for _ in minor4]
	g.append(make_ticks(radius,
		minor4,
		log_scale=log(100),
		length=2,
		stroke_width=0.1,
		stroke="black",
	))
	g.append(make_ticks(radius,
		minor3,
		log_scale=log(100),
		length=4,
		stroke_width=0.1,
		stroke="black",
	))
	g.append(make_ticks(radius,
		minor2,
		log_scale=log(100),
		length=6,
		stroke_width=0.2,
		stroke="black",
	))
	g.append(make_ticks(radius,
		minor1,
		log_scale=log(100),
		length=8,
		stroke_width=0.2,
		stroke="black",
	))
	g.append(make_tick_labels(radius,
		[[_, "%d" % _] for _ in major],
		10,
		log_scale=log(100),
		length=10,
		stroke_width=0.4,
		stroke="black",
		text_angle=90,
		pos=(2,-2),
	))

	#extra_labels = [[_/10, ".%d" % (_ % 10)] for _ in frange(11,20) + [25,35]]
	#extra_labels += [[pi, "π"]]
	#extra_labels += [[e, "e"]]
	g.append(make_tick_labels(radius,
		extra_labels,
		8,
		log_scale=log(100),
		text_angle=90,
		pos=(2,-2),
	))


	return g

def make_radians(radius):
	g = draw.Group()
	major = [[degrees(a), "%.1f" % (a)] for a in frange(0, 2*pi, 0.1)]

	g.append(draw.Circle(
		0, 0, radius,
		fill='none',
		stroke='black',
		stroke_width=0.1,
	))

	# replace the one close to pi and other special values
	extra_labels = [
	 [degrees(  pi/6), "π/6"],	# 30
	 [degrees(  pi/3), "π/3"],	# 60
	 [degrees(  pi/2), "π/2"],	# 90
	 [degrees(2*pi/3), "2π/3"],	# 120
	 [degrees(5*pi/6), "5π/6"],	# 150
	 [degrees(  pi  ), "π"],	# 180
	 [degrees(7*pi/6), "7π/6"],	# 210
	 [degrees(4*pi/3), "4π/3"],	# 240
	 [degrees(3*pi/2), "3π/2"],	# 270
	 [degrees(5*pi/3), "5π/3"],	# 300
	 [degrees(11*pi/6), "11π/6"],	# 330
	 [359, "2π"],	# 360
	]

	g.append(make_ticks(radius, [degrees(_) for _ in frange(0,2*pi,0.01)], 2, stroke_width=0.2))

	g.append(make_ticks(radius, [degrees(_) for _ in frange(0,2*pi,0.05)], 5, stroke_width=0.2))

	g.append(make_tick_labels(radius, major,
		10,
		text_angle=90,
		pos=(2,8),
		length=8,
		stroke="black",
		stroke_width=0.4,
	))

	g.append(make_tick_labels(radius, extra_labels,
		10,
		text_angle=90,
		pos=(0,-2),
		text_anchor="middle",
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
inner.append(make_semidiameter(h_e_radius))
inner.append(make_d_lines(390))

# Instructions for front side
inner.append(draw.Text(
"""
True Altitude
1. Point to zero on inner scale
2. Outer scale to minutes of Sextant Altitude (H
3. Point to index error on inner scale
3. Inner scale to Eye
4. Point to Height of Eye
5. Inner scale to upper/lower limb and month
6. Point to degrees of observed height and temperature
7. Outer scale now shows minutes of True Altitude (Ho)
""", 10, -250, -250,
stroke="none",
fill="black"
))


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
back.append(make_radians(400))

# 24-hour clock on the outsde
back.append(make_rule(440, 360/(24*2), 360/(24*4), 360/(24*60), fmt=lambda x: "%02d:%02d" % ((x // 15), (4 * (x % 15)))))

# 90 degree circle and sine/cosine tables
back.append(make_rule(370, 4, 1, 0.5, fmt=lambda x: "%.0f" % (x // 4)))
back.append(make_labels(370, 4, 0, 360, lambda x: "%.0f" % ((90 - x // 4) % 90), font_style="italic", fill="red", text_anchor="end", pos=(-2,-2)))
back.append(make_sine(352))
back.append(make_tangent_scale(334))

back.append(make_gha_scale(300))
back.append(make_sqrt_scale(240))


d.append(front)
d.append(back)
d.save_svg('rule.svg')

