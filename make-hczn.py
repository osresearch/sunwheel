#!/usr/bin/python3
# Generate a circular web diagram of a given lattitude
# that allows Hc and Zn to be read directly.
import drawsvg as draw
from math import radians, cos, sin, acos, asin, degrees

def haversine(x):
	return (1 - cos(x))/2
def ahaversine(y):
	if y < 0:
		y = 0
	if y > 1:
		y = 1
	return acos(1 - 2 * y)

def compute_hczn(lat,dec,lha):
	lat = radians(lat)
	dec = radians(dec)
	lha = radians(lha)
	hav_hc = haversine(lha) * cos(lat) * cos(dec) + haversine(lat - dec)
	#print(f"{lat=} {dec=} {lha=} => {hav_hc=}")
	hc = radians(90) - ahaversine(hav_hc)

	hav_zn = (cos(lat - hc) - sin(dec)) / (2 * cos(lat) * cos(hc))
	zn = degrees(ahaversine(hav_zn))

	# if the sun was to the west of us,
	# our local hour angle will be positive
	# and we have to adjust our computed heading
	if lha > 0:
		zn = 360 - zn

	return (degrees(hc),zn)


def compute_xy(r,a):
	a = radians(a + 180)
	return (r * sin(a), r * cos(a))


size = 1500
d = draw.Drawing(size,size, origin=(0,0))
d.append(draw.Rectangle(0, 0, size, size, fill='#fff'))
center = draw.Group(transform="translate(%d %d) scale(%.3f)" % (size/2, size/2, size/1000))

d.append_css("""
.label {
	fill: #000;
	stroke: none;
}
.red-label {
	fill: #f00;
	stroke: none;
	font-style: italic;
}
.thin {
	stroke: #000;
	stroke-width: 0.1;
	fill: none;
}
.thin-red {
	stroke: #f00;
	stroke-width: 0.5;
	fill: none;
}
.thick {
	stroke: #000;
	stroke-width: 0.5;
	fill: none;
}
.extra-thick {
	stroke: #000;
	stroke-width: 2;
	fill: none;
}
.thick-red {
	stroke: #f00;
	stroke-width: 0.5;
	fill: none;
}
""")


lat = 20
dec_max = 60
lha_max = 180
scale = 450


def make_hczn(lat):
	g = draw.Group()
	hc_scale = lambda hc: (90 - hc) * scale / 90
	for dec in range(-dec_max,dec_max+1):
		pts = []
		for lha in range(0,lha_max):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			pts += compute_xy(hc_scale(hc),zn)
		if len(pts) == 0:
			continue

		if dec == 0:
			c = "extra-thick"
		elif dec % 5 == 0:
			c = "thick"
		elif dec == 23 or dec == -23:
			c = "thin-red"
		else:
			c = "thin"
		g.append(draw.Lines(*pts, class_=c))

	for lha in range(0,lha_max):
		if lha == 0:
			continue
		pts = []
		for dec in range(-dec_max,dec_max+1):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			pts += compute_xy(hc_scale(hc),zn)

		if len(pts) == 0:
			continue
		g.append(draw.Lines(*pts, class_="thin" if lha % 10 else "thick"))

	# label the top of the chart
	for lha in range(0,lha_max+1,10):
		if lha == 0 or lha == 180 or lha == -180:
			continue

		(hc,zn) = compute_hczn(lat, dec_max+1, lha)
		if hc < 2:
			continue
		g.append(draw.Text("%+d" % (-lha), 10,
			*compute_xy(hc_scale(hc), zn),
			class_="label",
			text_anchor="middle",
		))
	for lha in range(0,lha_max+1,10):
		if lha == 0 or lha == 180 or lha == -180:
			continue

		(hc,zn) = compute_hczn(lat, dec_max+3, lha)
		if hc < 2:
			continue
		g.append(draw.Text("%+d" % (lha), 10,
			*compute_xy(hc_scale(hc), zn),
			class_="red-label",
			text_anchor="middle",
		))

	# label the declinations
	for lha in range(0,lha_max+1,30): #[-90,-60,-30,0,+30,+60,+90]:
		for dec in range(-dec_max+10,dec_max,10):
			if dec == 0 or lha == 180:
				continue
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < radians(1):
				continue
			(x,y) = compute_xy(hc_scale(hc), zn)
			g.append(draw.Text("%+d" % (dec), 10,
				x, y,
				class_="label",
				text_anchor="end" if lha > 0 else "start",
				dominant_baseline="auto" if dec < 0 else "hanging",
			))
	return g

def make_compass(r):
	g = draw.Group()
	g.append(draw.Circle(r=r, cx=0, cy=0, class_="thin"))

	for a in range(180,360):
		if a % 45 == 0:
			c = "extra-thick"
			l = 10
		elif a % 10 == 0:
			c = "thick"
			l = 10
		else:
			c = "thin"
			l = 5
		g.append(draw.Lines(
			*compute_xy(r,a),
			*compute_xy(r+l,a),
			class_=c,
		))
	# LHA=0 vertical line
	g.append(draw.Lines(
		0,-r - 10,
		0,+r + 10,
		class_="extra-thick",
	))

	# east/west lines are split so they
	# don't overlap with the grid
#	g.append(draw.Lines(
#		-r - 10,0,
#		-r + 50,0,
#		class_="extra-thick",
#	))
	g.append(draw.Lines(
		+r - 50,0,
		+r + 10,0,
		class_="extra-thick",
	))

	g.append(draw.Lines(
		-50,0,
		+50,0,
		class_="extra-thick",
	))

	# heading markings
	labels = {
		0: ("N",90,"middle"),
		90: ("E",0,"start"),
		180: ("S",90,"middle"),
		270: ("W",-180,"end"),
	}

	# black going one way
	for a in range(0,181,10):
		(t,rot,anchor) = labels.get(a, (
			"%d" % (a),
			0 if a < 180 else -180,
			"start" if a < 180 else "end",
		))
		g.append(draw.Text(t, 10,
			0, 0,
			transform="rotate(%d) translate(%.3f) rotate(%d)" % (a - 90+0, r+13, rot),
			text_anchor=anchor,
			dominant_baseline="hanging",
			class_="label",
		))

	# red going the other
	for a in range(190,360,10):
		(t,rot,anchor) = labels.get(a, (
			"%d" % (a),
			0,
			"start",
		))
		g.append(draw.Text(t, 10,
			0, 0,
			transform="rotate(%d) translate(%.3f) rotate(%d)" % (-a-90-0, r+13, rot),
			text_anchor=anchor,
			dominant_baseline="auto",
			class_="red-label",
		))
	return g

def make_height(r):
	g = draw.Group()
	g.append(draw.Circle(r=r, cx=0, cy=0, class_="thin"))

	for a in range(0,90*3):
		if a % (10*3) == 0:
			c = "extra-thick"
			l = 10
		elif a % 3 == 0:
			c = "thick"
			l = 8
		else:
			c = "thin"
			l = 5
		g.append(draw.Lines(
			*compute_xy(r,2*a/3),
			*compute_xy(r+l,2*a/3),
			class_=c,
			))

	for a in range(0,90,1):
		t = "%d" % (a)
		rot = 180
		anchor = "end"
		g.append(draw.Text(t, 10,
			0, -3,
			transform="rotate(%d) translate(%.3f) rotate(%d)" % (2*a+90, r+5, rot),
			text_anchor=anchor,
			dominant_baseline="bottom",
			class_="label",
		  ))
	return g

def make_chart(lat):
	g = draw.Group()
	g.append(make_hczn(lat))
	g.append(make_compass(scale))

	g.append(make_hc(lat))
	g.append(make_height(scale))

	g.append(draw.Circle(r=5, cx=0, cy=0, fill="#000"))

	g.append(draw.Text("Lat %d" % (lat), 30,
		-450,-450,
		class_="label",
		font_weight="bold",
	))
	return g


def make_lots():
	x = 0
	y = 0
	for lat in range(0,60,5):
		print(lat)
		g = draw.Group(transform="translate(%d %d) scale(0.3) translate(500 500)" % (x,y))
		g.append(make_chart(lat))
		d.append(g)

		x += 300
		if x > 900:
			x = 0
			y += 300

# just a vertical chart for the hc computation
# full page vertical angle from 0 to 90
def make_hc(lat):
	g = draw.Group()
	max_dec = 23

	scale_zn = lambda dec: (dec + max_dec) * (scale-150) / (2*max_dec) + 150

	for lha in range(0,180):
		pts = []
		for dec in range(-max_dec,max_dec+1):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			pts += compute_xy(scale_zn(dec), 180 - hc * 2)
		if len(pts) == 0:
			continue
		g.append(draw.Lines(*pts, class_="thick" if lha % 10 == 0 else "thin"))
	for dec in range(-max_dec,max_dec+1):
		pts = []
		for lha in range(0,180):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0:
				continue
			pts += compute_xy(scale_zn(dec), 180 - hc * 2)
		if len(pts) == 0:
			continue

		if dec == 0:
			c = "extra-thick"
		elif dec % 5 == 0:
			c = "thick"
		else:
			c = "thin"

		g.append(draw.Lines(*pts, class_=c))

	for lha in [0,30,60,90]:
		for dec in range(-20,21,5):
			(hc,zn) = compute_hczn(lat, dec, lha)
			if hc < 0 or dec == 0:
				continue
			g.append(draw.Text("%+d" % (dec), 10,
				*compute_xy(scale_zn(dec), 180 - hc * 2),
				text_anchor="end",
				class_="label" if dec > 0 else "red-label",
			))
	dec = -max_dec
	for lha in range(10,90,10):
		(hc,zn) = compute_hczn(lat, dec, lha)
		if hc < 0:
			continue
		g.append(draw.Text("%d" % (lha), 10,
			*compute_xy(scale_zn(dec), 180 - hc * 2),
			class_="label",
		))
	return g

center.append(make_chart(lat))
#d.append(make_lots())

d.append(center)
d.save_svg("hczn.svg")

d.save_png("hczn.png")


