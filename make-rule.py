#!/usr/bin/env python3
# Generates the slide rule elements using SVG

from math import sqrt, sin, cos, tan, atan2, ceil, radians, degrees, asin, acos, log, pi, e, atan
import drawsvg as draw
import datetime
import sys
import re

year = 2020 # for equation of time
pointer_angle = 0
inner_angle = 0
outer_angle = 0
draw_back = True
output_file = "rule.svg"

if len(sys.argv) > 1 and sys.argv[1].endswith(".png"):
	# special case for the makefiles where
	# all the parameters are in the file name
	output_file = sys.argv[1]
	group = re.match(r".*-(.*),(.*),(.*)\.png", output_file)
	if not group:
		print("unable to parse file name", file=sys.stderr)
		sys.exit(-1)
	pointer_angle = float(group[1])*6
	inner_angle = float(group[2])*6
	outer_angle = float(group[3])*6
	draw_back = 0
elif len(sys.argv) > 1:
	pointer_angle = float(sys.argv[1])
if len(sys.argv) > 2:
	inner_angle = float(sys.argv[2])
if len(sys.argv) > 3:
	outer_angle = float(sys.argv[3])
if len(sys.argv) > 4:
	draw_back = int(sys.argv[4])

if len(sys.argv) > 5:
	output_file = sys.argv[5]


d = draw.Drawing(2000 if draw_back else 1000,1000, origin=(0,0))

def compute_position(radius, angle, length, log_scale=False, spiral=False):
	length = 10 # always force same spiral in
	if log_scale:
		angle = log(angle) * 360 / log_scale
	if spiral:
		radius += (angle / 360) * length * 2.25
	return (radius, angle)

def compute_xy(r,a):
	return (r * cos(radians(a)), r * sin(radians(a)))


def draw_spiral(radius, pts, log_scale, stroke='black', stroke_width=0.1):
	arcs = []
	for angle in pts:
		(r,a) = compute_position(radius,angle,10,log_scale,True)
		(x,y) = compute_xy(r,a)
		arcs.append(x)
		arcs.append(y)
	return draw.Lines(*arcs,
		fill='none',
		stroke=stroke,
		stroke_width=stroke_width,
	)

def make_ticks(radius, ticks, length, log_scale=None, stroke='black', spiral=False, **style):
	g = draw.Group()
	for angle in ticks:
		(r,a) = compute_position(radius, angle, length, log_scale, spiral)
		g.append(draw.Line(
			-length,0,length,0,
			fill='none',
			stroke=stroke,
			transform="rotate(%.3f) translate(%.3f)" % (a,r),
			**style,
		))
	return g

def make_labels(radius, step, start, end, fmter, pos=(1,9), size=10, text_angle=+90, fill="black", **style):
	g = draw.Group()
	m = start
	while m < end:
		s = fmter(m) #"%.0f" % (m)
		g.append(draw.Text(s, size, pos[0], pos[1],
			#align="left",
			fill=fill,
			stroke='none',
			transform="rotate(%.3f) translate(%.3f) rotate(%.3f)" % (m,radius,text_angle),
			**style,
		))
		m += step
	return g

def make_tick_labels(radius, labels, size=10, log_scale=None, align="right", text_angle=0, pos=(0,0), fill="black", stroke=None, stroke_width=0.3, length=0, spiral=False, **style):
	g = draw.Group()
	for (angle,label) in labels:
		(r,a) = compute_position(radius, angle, length, log_scale, spiral)
		g.append(draw.Text(label, size, pos[0], pos[1],
			align=align,
			fill=fill,
			stroke='none',
			transform="rotate(%.3f) translate(%.3f) rotate(%.3f)" % (a, r, text_angle),
			**style,
		))

	if length > 0:
		g.append(make_ticks(
			radius,
			[x[0] for x in labels],
			length,
			log_scale=log_scale,
			spiral=spiral,
			stroke=stroke,
			stroke_width=stroke_width,
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

def make_rule(radius, major, minor1, minor2, minor3=None, fmt=deg2sec, pos=(1,9), start=0, end=360, size=10):
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
	g.append(make_ticks(radius, frange(start, end, major),  10, stroke_width=0.4))
	g.append(make_labels(radius, major, start, end, fmt, pos=pos, size=size))
	return g


# Height of eye is 1.76 sqrt(H_e) in meters
def height_of_eye(H_e):
	return 1.76 * sqrt(H_e) * 6

def make_height_of_eye(radius,angle):
	g = draw.Group(transform="rotate(%.3f)" % (angle))
	major = [height_of_eye(H_e) for H_e in frange(0,20.1,1)]
	minor1 = [height_of_eye(H_e) for H_e in frange(0,20,0.5)]
	minor2 = [height_of_eye(H_e) for H_e in frange(0,5,0.1)]
	minor2 += [height_of_eye(H_e) for H_e in frange(5,10,0.25)]

	g.append(make_ticks(radius-10, minor2, 4, stroke_width=0.1))
	g.append(make_ticks(radius-10, minor1, 8, stroke_width=0.2))
	g.append(make_ticks(radius-10, major,  15, stroke_width=0.3))

	# Meters
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
		[[height_of_eye(21.5), "m"]],
		pos=(-10,+3),
		text_anchor="end",
		#stroke="red",
		#length=8,
		#stroke_width=0.4,
	))

	# Feet
	ft_radius = radius - 50
	ft_per_m = 3.281
	major = [height_of_eye(H_e/ft_per_m) for H_e in frange(0,65.1,5)]
	minor1 = [height_of_eye(H_e/ft_per_m) for H_e in frange(0,65.1,1)]

	labels = [[height_of_eye(h_e/ft_per_m), "%.0f" % (h_e)] for h_e in
		[5,10,15,20,25,30,35,40,45,50,55,60,65]]

	g.append(make_ticks(ft_radius, minor1,  8, stroke_width=0.2))
	g.append(make_ticks(ft_radius, major,  15, stroke_width=0.3))
	g.append(make_tick_labels(
		ft_radius,
		labels,
		pos=(-10,+3),
		text_anchor="end",
	))
	g.append(make_tick_labels(
		ft_radius,
		[[height_of_eye(21.5), "ft"]],
		pos=(-10,+3),
		text_anchor="end",
		#stroke="red",
		#length=8,
		#stroke_width=0.4,
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
def make_refraction(radius, angle):
	sd_1 = 16.2
	sd_2 = 15.9
	g = draw.Group(transform="rotate(%.3f)" % (angle))
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
		g.append(draw.Text(
			"%d°F" % (t * 9/5 + 32),
			8.5, -8, -2,
			transform="rotate(%f) translate(%f)" % (refraction(3,1010,t), r),
			text_anchor="center",
		))
		g.append(draw.Text(
			"%d°C" % (t),
			8.5, -8, +10,
			transform="translate(%f)" % (r),
			text_anchor="center",
		))

	g.append(make_tick_labels(
		radius,
		[[refraction(a,1010,-9), "%.0f" % (a)] for a in majors],
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

#	g.append(make_tick_labels(
#		radius-25,
#		[
#			[+sd_1*6-4, "Upper"],
#			[-sd_1*6-2, "Lower"],
#		],
#		text_anchor="center",
#		size=8,
#	))

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
	g = draw.Group(transform="rotate(0)")
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

	for scale in [-1]:
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
	inner_step = 290

	radius = lambda d: outer_radius - inner_step * (1-d)

	# horizontal lines for the different values of d
	for d in frange(0.1, 1.1, 0.1):
		r = radius(d)
		g.append(make_arcs(frange(-12, 12.01, 0.1), lambda t: (r, t*d*6), stroke_width=0.1))

		if d < 0.2 or d > 0.9:
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
		stroke = "black"
		width = 0.5

		if t == 0:
			width = 2
		elif t == -6 or t == 6:
			stroke = "red"
			width = 1
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
	for a in frange(2, 10, 1) + [10,12,14,20,30,80]:
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


# Sine is one quadrant for increased accuracy and makes two circles
# for 0.01 to 0.1 and 0.1 to 1.0
def make_log_sine(radius):
	g = draw.Group()

	# start at -20 since we will spiral outwards for the larger angles
	#radius -= 20

	major = []
	minor1 = []
	minor2 = []
	minor3 = []
	minor4 = []

	# sine 0.56 - 5.6 degrees
	for a in frange(0.5, 4.51, 0.1) + frange(4.6, 6.01, 0.2):
		major.append(sin(radians(a)))
	for a in frange(0.50, 6.001, 0.05):
		minor1.append(sin(radians(a)))
	for a in frange(0.50, 6.001, 0.01):
		minor2.append(sin(radians(a)))
	for a in frange(0.50, 1.801, 0.005):
		minor3.append(sin(radians(a)))
	#for a in frange(0.58, 1.801, 0.005):
		#minor3.append(sin(radians(a)))

	# sine 5.6 - 90 degrees
	for a in frange(6, 40.1, 1) + frange(45, 80, 5) + frange(80,90.1,10):
		major.append(sin(radians(a)))
	for a in frange(6, 80, 0.5) + frange(80,90,1):
		minor1.append(sin(radians(a)))
	for a in frange(6, 40, 0.1) + frange(40,75,0.25):
		minor2.append(sin(radians(a)))


	g.append(make_logscale(radius, "", # we will label
		major,
		minor1,
		minor2,
		minor3,
		[],
		fmt=lambda x: ("%.1f" if x < 0.14 else "%.0f") % (degrees(asin(x))),
		#fmt=lambda x: "%.1f" % (degrees(asin(x))),
		log_scale=log(10),
		extra_labels=[],
		spiral=True,
	))

	# cosine is reverse of sin in red
	g.append(make_tick_labels(radius,
		[[x, ("%.1f" if x < 0.104 else "%.0f") % (90 - degrees(asin(x)))] for x in major],
		8,
		log_scale=log(10),
		spiral=True,
		text_angle=90,
		text_anchor="end",
		fill="red",
	))

	# a faint divider to separate the sine and tangent
	g.append(draw_spiral(
		radius-15,
		[sin(radians(x)) for x in frange(0.50, 4.7, 0.01)],
		log_scale=log(10),
		stroke="green",
		stroke_width=0.3,
	))

	return g

# 0 to 45 and 45 to 90
def make_log_tangent(radius):
	g = draw.Group()

	major = []
	minor1 = []
	minor2 = []
	minor3 = []

	# tan(5.7) to 45 is 0.1 to 1.0
	for a in frange(2, 45, 1) + frange(45,83.1,1):
		major.append(tan(radians(a)))
	for a in frange(2, 83.1, 0.5):
		minor1.append(tan(radians(a)))
	for a in frange(2, 83.1, 0.1):
		minor2.append(tan(radians(a)))
	for a in frange(2, 20, 0.05) + frange(70,83.001, 0.05):
		minor3.append(tan(radians(a)))

	g.append(make_logscale(radius, "T",
		major,
		minor1,
		minor2,
		minor3,
		[],
		fmt=lambda x: "%.0f" % (degrees(atan(x))),
		log_scale=log(10),
		spiral=True,
		extra_labels=[],
	))

	# cotan is in reverse in red
	g.append(make_tick_labels(radius,
		[[x, "%.0f" % (90 - degrees(atan(x)))] for x in major],
		8,
		log_scale=log(10),
		spiral=True,
		text_angle=90,
		text_anchor="end",
		fill="red",
	))

	return g

# Sine is one quadrant for increased accuracy
def make_sine(radius):
	g = draw.Group()
	labels = []
	extra_labels = []
	minor1 = []
	minor2 = []
	minor3 = []
	for a in frange(0,0.9001,0.05):
		labels.append([degrees(asin(a)*4), "%.2f" % (a)])
	for a in frange(0.91,0.951,0.01):
		extra_labels.append([degrees(asin(a)*4), "%.2f" % (a)])
	for a in frange(0.955,0.99999,0.005):
		extra_labels.append([degrees(asin(a)*4), "%.3f" % (a)])

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
		size=10,
		length=8,
		stroke_width=0.4,
		stroke="black",
	))
	g.append(make_tick_labels(radius, extra_labels,
		size=8,
		text_angle=90,
		pos=(1,9),
		length=7,
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

def make_logscale(radius, label, major, minor1, minor2, minor3, minor4,
	log_scale=log(10),
	extra_labels=None,
	fmt=lambda x: "%d" % (x),
	text_anchor="start",
	pos=(2,+10),
	spiral=False,
	**kwargs
):
	g = draw.Group()
	(label_r,label_a) = compute_position(radius, major[0], 9, log_scale, spiral)
	g.append(draw.Text(label, 9, +12, +8,
		font_style="bold",
		fill="blue",
		stroke="none",
		text_anchor="start",
		transform="rotate(%.3f) translate(%3.f) rotate(+90)" % (label_a, label_r),
	))
	if not spiral:
		g.append(draw.Circle(
			0, 0, radius,
			fill='none',
			stroke='black',
			stroke_width=0.1,
		))
	else:
		g.append(draw_spiral(
			radius,
			minor2,
			log_scale=log_scale,
			stroke="black",
			stroke_width=0.1,
		))
	g.append(make_ticks(radius,
		minor4,
		log_scale=log_scale,
		length=2,
		stroke_width=0.1,
		stroke="black",
		spiral=spiral,
	))
	g.append(make_ticks(radius,
		minor3,
		log_scale=log_scale,
		length=4,
		stroke_width=0.1,
		stroke="black",
		spiral=spiral,
	))
	g.append(make_ticks(radius,
		minor2,
		log_scale=log_scale,
		length=6,
		stroke_width=0.2,
		stroke="black",
		spiral=spiral,
	))
	g.append(make_ticks(radius,
		minor1,
		log_scale=log_scale,
		length=8,
		stroke_width=0.3,
		stroke="black",
		spiral=spiral,
	))
	g.append(make_tick_labels(radius,
		[[_, fmt(_)] for _ in major],
		10,
		log_scale=log_scale,
		length=10,
		stroke_width=0.5,
		stroke="black",
		spiral=spiral,
		text_angle=90,
		text_anchor=text_anchor,
		pos=pos,
		**kwargs
	))

	if extra_labels:
		g.append(make_tick_labels(radius,
			extra_labels,
			8,
			log_scale=log_scale,
			text_angle=90,
			length=3,
			stroke="red",
			stroke_width=0.3,
			spiral=spiral,
			text_anchor=text_anchor,
			pos=(pos[0],pos[1]-2),
			**kwargs
		))

	return g
#
# This makes three scales:
# X^2, X, and 1/X
# You can also compute:
# sqrt(Y) by going X^2 -> X
# 1/sqrt(Y) by going X^2 -> 1/X
#
def make_sqrt_scale(radius,draw_inverse):
	g = draw.Group()

	major = frange(1,10)
	minor1 = frange(1,10,0.5)
	minor2 = frange(1,10,0.1)
	minor3 = frange(1,10,0.05)
	minor4 = frange(1,6, 0.01) + frange(6,10,0.025)

	extra_points = frange(11,20) + [25,35,45,55,65,75]

	extra_labels = [[_/10, "%.1f" % (_/10)] for _ in extra_points]
	extra_labels += [[pi, "π"]]
	extra_labels += [[e, "e"]]
	extra_labels += [[sqrt(2), "_√2"]]
	extra_labels += [[degrees(1), "r"]]
	extra_labels += [[0.00134102, "W"]]
	extra_labels += [[2.54, "mm"]]
	extra_labels += [[2.2, "kg"]]
	extra_labels += [[1/0.5399, "km"]]

	# the X scale goes up to 10
	g.append(make_logscale(radius, "X",
		major,
		minor1,
		minor2,
		minor3,
		minor4,
		log_scale=log(10),
		extra_labels=extra_labels,
	))

	if draw_inverse:
		# Draw the scales in reverse to make the 1/X scale
		g.append(make_logscale(radius-20, "1/X",
			[10,2] + major[2:],
			minor1,
			minor2,
			minor3,
			minor4,
			fill="red",
			log_scale=log(0.1),
			fmt=lambda x: "%.01f" % (x/10),
			text_anchor="end",  # left side of the line
			pos=(-2,+10),
			extra_labels = [[_, "%.02f" % (_/100)] for _ in extra_points],
		))
	else:
		# double the scales to go up to 100 for the X^2 on the outside
		g.append(make_logscale(radius+20, "X²",
			major + [10 * _ for _ in major],
			minor1 + [10 * _ for _ in minor1],
			minor2 + [10 * _ for _ in minor2],
			minor3 + [10 * _ for _ in minor3],
			minor4 + [10 * _ for _ in minor4],
			log_scale=log(100),
			extra_labels=extra_labels + [[_, "%d" % (_)] for _ in extra_points],
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
		8,
		text_angle=90,
		pos=(2,8),
		length=8,
		stroke="black",
		stroke_width=0.4,
	))

	g.append(make_tick_labels(radius, extra_labels,
		8,
		text_angle=90,
		pos=(0,-2),
		text_anchor="middle",
	))
		
	return g

def make_minutes(radius):
	g = draw.Group()

	major = frange(0,360,360/60)
	minor1 = frange(0,360,360/120)
	minor2 = frange(0,360,360/600)

	g.append(make_ticks(radius, minor2, 8, stroke_width=0.2))
	g.append(make_ticks(radius, minor1, 12, stroke_width=0.3))
	g.append(make_ticks(radius, major, 20, stroke_width=0.5))
	g.append(draw.Circle(0, 0, radius, fill="none", stroke="black", stroke_width=0.5))

	# 0-60 minutes around the circle in black
	#g.append(make_rule(radius, 360/60, 360/120, 360/600, pos=(2,9)))
	# black numbers going clockwise
	g.append(make_labels(radius, 6, 0, 360,
		lambda x: "%.0f" % ((x/6) % 60),
		size=14,
		pos=(2,12),
		text_anchor="start",
		fill="black",
	))

	# red numbers going reverse around the circle
	g.append(make_labels(radius, 6, 0, 360,
		lambda x: "%.0f" % ((60-x/6) % 60),
		pos=(-3,-5),
		size=14,
		text_anchor="end",
		fill="red",
		font_style="italic",
	))

	# heavy red line to mark the zero and +/- for the crossing
	g.append(draw.Line(radius-10, 0, radius+10, 0, stroke="red", stroke_width=3))

#	g.append(draw.Text("+", 30,
#		2, -radius,
#		fill="black",
#		transform="rotate(90)",
#	))
#	g.append(draw.Text("-", 30,
#		-20, -radius+15,
#		fill="black",
#		transform="rotate(90)",
#	))
		

	return g


# minutes that the sun is ahead of noon
def equation_of_time(d,y=year):
	D = 6.24004077 + 0.01720197 * (365.25 * (y-2000) + d)
	return -7.659 * sin(D) + 9.863 * sin(2*D + 3.5932)

def julian(m,d,y=year):
	return int(datetime.date(y,m,d).strftime("%j"))
	

def eq_time_radius(d):
	if d < julian(2,11):
		return -45
	if d < julian(5,15):
		return -0
	if d < julian(7,30):
		return -15
	if d < julian(10,31):
		return -30
	return -45

months = [
	["Jan",31,(+6,-1)],
	["Feb",28,(+6,-1)],
	["Mar",31,(-6,+6)],
	["Apr",30,(-6,+6)],
	["May",31,(-7,+5)],
	["Jun",30,(+6,-2)],
	["Jul",31,(+5,-2)],
	["Aug",31,(+8,+5)],
	["Sep",30,(+6,+5)],
	["Oct",31,(-6,+6)],
	["Nov",30,(+8,-2)],
	["Dec",31,(+6,-2)],
]

def make_equation_of_time(radius):
	g = draw.Group()
	pts = []
	#r = lambda d: radius/2 + 30 * sin(2*pi*d/365 + 0.95)
	r = lambda d: radius + eq_time_radius(d)
	for d in range(0,366):
		minutes = equation_of_time(d)
		(x,y) = compute_xy(r(d), minutes*6)
		pts.append(x)
		pts.append(y)
	g.append(draw.Lines(*pts, stroke="black", stroke_width=0.2, fill="none"))

	d = 0
	for (name,d_in_month,label_pos) in months:
		minutes = equation_of_time(d)

		g.append(draw.Line(-5,0,+5,0,
			stroke="black",
			stroke_width=0.5,
			fill="none",
			transform="rotate(%.3f) translate(%.3f)" % (minutes*6, r(d)),
		))

		for d_of_month in range(1,d_in_month):
			d_minutes = equation_of_time(d + d_of_month)
			g.append(draw.Line(-1,0,+1,0,
				stroke="black",
				stroke_width=0.1,
				fill="none",
				transform="rotate(%.3f) translate(%.3f)" % (d_minutes*6, r(d+d_of_month)),
			))
		for d_of_month in range(7,d_in_month,7):
			d_minutes = equation_of_time(d + d_of_month)
			g.append(draw.Line(-3,0,+3,0,
				stroke="black",
				stroke_width=0.2,
				fill="none",
				transform="rotate(%.3f) translate(%.3f)" % (d_minutes*6, r(d+d_of_month)),
			))

		g.append(draw.Text(name, 7, *label_pos,
			fill="black",
			text_anchor="middle",
			transform="rotate(%.3f) translate(%.3f)" % (minutes*6, r(d)),
		))
		d += d_in_month
			
	return g


def make_sin_sin_scale(radius):
	g = draw.Group(id="sinsin")

	# scale on the outside goes from 0 to 0.4 (sin(23))
	max_scale = 0.42
	output_angle = lambda x: 0 if x == 0 else radians(log(max_scale) * 360 / log(x))
	#output_angle = lambda x: 0 if x == 0 else radians(x * 180 / max_scale)
	output_radius = lambda l: radius - 150*sin(radians(l))
	for o in frange(0.001,0.01,0.001):
		g.append(draw.Text("%.3f" % (o),
			5, 0, 0,
			text_anchor="middle",
			transform="rotate(%.3f) translate(%.3f)" % (degrees(output_angle(o)), radius),
		))
	for o in frange(0.01, 0.4, 0.01):
		g.append(draw.Text("%.2f" % (o),
			5, 0, 0,
			text_anchor="middle",
			#transform="rotate(%.3f) translate(%.3f)" % (degrees(output_angle(o)), radius - 100/ log(o) * log(max_scale)),
			transform="rotate(%.3f) translate(%.3f)" % (degrees(output_angle(o)), radius),
		))

	for d in [0.1, 0.25, 0.5] + frange(1,25.1,1):
		pts = []
		for l in frange(1,90.1,1):
			# compute the angle that provides correct output
			# for sin(d)*sin(l)
			o = sin(radians(d)) * sin(radians(l))
			a = output_angle(o)
			r = output_radius(l)

			pts.append(r * cos(a))
			pts.append(r * sin(a))

		g.append(draw.Lines(*pts,
			fill="none",
			stroke="black",
			stroke_width=0.1 if d % 5 != 0 else 0.5,
		))

		if d < 1:
			continue
		g.append(draw.Text("%.0f" % (d), 5, 0, 0,
			text_anchor="middle",
			transform="rotate(%.3f) translate(%.3f) rotate(-90)" % (degrees(output_angle(sin(radians(d)))), output_radius(90)),
		))


	for l in frange(0,90.1,5):
		pts = []
		for d in frange(0.01,25.01,0.01):
			o = sin(radians(d)) * sin(radians(l))
			a = output_angle(o)
			r = output_radius(l)

			pts.append(r * cos(a))
			pts.append(r * sin(a))
		g.append(draw.Lines(*pts,
			fill="none",
			stroke="black",
			stroke_width=0.1,
		))
	for l in frange(0,90.1,10):
		pts = []
		for d in frange(0.01,25.01,0.01):
			o = sin(radians(d)) * sin(radians(l))
			a = output_angle(o)
			r = output_radius(l)

			pts.append(r * cos(a))
			pts.append(r * sin(a))
		g.append(draw.Lines(*pts,
			fill="none",
			stroke="black",
			stroke_width=0.2,
		))
			#g.append(draw.Text("%.2f" % v, 7, radius, 0,
				#transform="rotate(%.3f) translate(%.3f)" % ())

	return g

def make_360_clock(radius):
	g = draw.Group()
	g.append(make_rule(radius-20, 5, 1, 0.5,
		size=7,
		fmt=lambda x: "%.0f" % (x)))
	g.append(make_labels(radius-20, 5, 0, 360,
		lambda x: "%.0f" % ((360-x) % 360),
		size=7,
		pos=(-2,-1), text_anchor="end", fill="red", font_style="italic",
	))
	#g.append(make_radians(radius-40))

	# 24-hour clock on the outsde and inverted in red
	g.append(make_rule(radius, 360/(24), 360/(24*4), 360/(24*60),
		size=9,
		fmt=lambda x: "%02d:%02d" % ((x // 15), (4 * (x % 15))),
	))
	g.append(make_labels(radius, 360/(24), 0, 360,
		lambda x: "%02d:%02d" % ((24+12 - ((x+14) // 15)) % 24, (4 * (x % 15))),
		size=9,
		pos=(-2,-1), text_anchor="end", fill="red", font_style="italic",
	))

	return g

####
#### Front side
####
# Outer rules for 0-360 degrees with negative markers
front = draw.Group(transform="translate(500 500)")


outer = draw.Group(transform="rotate(%.3f)" % (-outer_angle), id="outer")
outer.append(make_minutes(430))

inner = draw.Group(transform="rotate(%.3f)" % (-inner_angle), id="inner")
inner.append(make_minutes(390))

#inner.append(make_rule(400, 360/60, 360/120, 360/600))
# add an reverse scale for the inner ring
#inner.append(make_labels(400, 6, 0, 360, lambda x: "-%.0f" % ((60-x/6) % 60), pos=(-2,-2), text_anchor="end", fill="red", font_style="italic"))

h_e_radius = 360
inner.append(make_height_of_eye(h_e_radius, -180))

# The refraction, parallax and semi diameter can all be done with
# the one Altitude Correction Table (ACT)
inner.append(make_refraction(h_e_radius, -180))
inner.append(make_semidiameter(h_e_radius))
inner.append(make_d_lines(h_e_radius+10))

inner.append(make_equation_of_time(100))

# Cut lines
inner.append(draw.Circle(0,0, 10, fill="none", stroke="black", stroke_width=1))
outer.append(draw.Circle(0,0, 410, fill="none", stroke="black", stroke_width=1))
outer.append(draw.Circle(0,0, 450, fill="none", stroke="black", stroke_width=1))

pointer = draw.Group(transform="rotate(%.3f)" % (pointer_angle), id="pointer")
pointer.append(draw.Line(0,0, 500, 0, fill="none", stroke="blue", stroke_width=2))
pointer.append(draw.Line(0,0, -500, 0, fill="none", stroke="none", stroke_width=2))
front.append(pointer)
front.append(outer)
front.append(inner)

inner.append(draw.Image(-250, -300, 250, 250, path="latitude.svg", embed=True))



####
#### Reverse side (no rotating parts)
####
back = draw.Group(transform="translate(1500 500) rotate(%.3f)" % (+outer_angle))
back.append(pointer)
back.append(draw.Circle(0,0, 10, fill="none", stroke="black", stroke_width=1))
back.append(draw.Circle(0,0, 410, fill="none", stroke="black", stroke_width=1))
back.append(draw.Circle(0,0, 450, fill="none", stroke="black", stroke_width=1))

outer = draw.Group(id="back_outer")
inner = draw.Group(id="back_inner")

# rule for 360 degree circle with reverse angles as well
inner.append(make_360_clock(235))

# 90 degree circle and sine/cosine tables
#back.append(make_rule(365, 4, 1, 0.5, fmt=lambda x: "%.0f" % (x // 4)))
#back.append(make_labels(365, 4, 0, 360, lambda x: "%.0f" % ((90 - x // 4) % 90), font_style="italic", fill="red", text_anchor="end", pos=(-2,-2)))
#back.append(make_sine(345))

#back.append(make_gha_scale(240))

outer.append(make_sqrt_scale(420, False))
inner.append(make_sqrt_scale(400, True))
inner.append(make_log_sine(360))
inner.append(make_log_tangent(285))


#back.append(make_log_cosine(320))
#back.append(make_sin_sin_scale(200))

back.append(outer)
back.append(inner)

d.append(front)
d.append(back)

if output_file.endswith(".png"):
	d.save_png(output_file)
else:
	d.save_svg(output_file)
#d.save_png('rule.png')

