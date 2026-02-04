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

from sliderule import *
import datetime
import sys
import re

# should these be in sliderule?
cut = 420
outer_cut = 500

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
def make_lunar_dist(R, offset = 150):
	g = draw.Group()
	min_d = 25
	max_d = 35
	#def r_func(d,m): return offset + (R - offset) * (max_d-d) / 10
	def r_func(d,m): return offset + (R - offset) * (d-min_d) / 10
	def a_func(d,m): return m * d / 100 / 6

	g2 = draw.Group(id_="time-rings")

	for d in range(min_d,max_d+1):
		pts = []
		pts2 = []
		for m in range(0, 60*60+1, 1):
			a = a_func(d,m)
			r = r_func(d,m)
			pts += compute_xy(r, a)
			pts2 += compute_xy(r, -a)

			if False and m % (60*10) == 0 and d % 2 == 0:
				g2.append(draw.Text("%d" % (d), 11,
					*compute_xy(r, a),
					class_="red_angle",
				))
					
		if d == 30:
			c = "extra_thick"
		else:
			c = "thin"
		g2.append(draw.Lines(*pts,
			class_=c,
			id_="time-ring-%02d" % (d),
		))

		if d != max_d:
			g2.append(draw.Text("%d" % (d), 11,
				0, 7,
				class_="angle",
				transform="translate(%.3f %.3f) rotate(-90)" % (r_func(d,0), 0),
			))
		#g.append(draw.Lines(*pts2, class_=c))
	g.append(g2)
	g2 = draw.Group(id_="time-lines")

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
		g2.append(draw.Lines(*pts,
			class_=c,
			id_="time-line-%02d" % (m),
		))

		if m % (60*1) != 0 or m == 0 or m == 60*60:
			continue

		# add some labels
		for label_d in [max_d-4, min_d-2]:
			if label_d == min_d - 2 and m % (60*5) != 0:
				continue

			pts = []
			for d in range(1,5):
				pts += compute_xy(r_func(label_d+d, m+3), a_func(label_d+d, m+3))
			path = draw.Lines(*pts)
			g2.append(draw.Text("%02d" % (m // (60)),
				11,
				path=path,
				text_anchor="end",
				dominant_baseline="hanging",
				class_="angle",
			))

	g.append(g2)
	
	return g


# Correct for "parallax in altitude"
# which ranges from 54 to 61.5
# and depends on the cosine of the altitude
# the semi diameter of the moon varies from 14.7 to 16.6
# this is a really weird diagram...
def make_lunar_parallax(R, offset=200):
	g = draw.Group()
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

	sd_coeff = 0.2724
	mid_angle = -sd_coeff * (hp_min+hp_max)/2 * 6
	if False: g.append(text_circle("Lunar semi-diameter", 10,
		offset-40,
		start=mid_angle-30,
		end=mid_angle+30,
		text_anchor="middle",
		class_="red_angle",
	))
	g.append(draw.Text("SD augmentation", 10,
		0, +10,
		class_="red_angle",
		text_anchor="start",
		transform="translate(%d %d) rotate(%.2f)" % (offset, -0, -8),
	))

	for hp in frange(hp_min, hp_max + 0.01, 0.5):
		# todo: include latitude offset hp * sin2(lat) / 298.3?
		# this seems very small so we'll ignore it
		for lat in []: # frange(0,91,30):
			a = hp * sin(radians(lat))**2 / 298.3
			r = r_func(hp,lat)
			g.append(draw.Lines(
				*compute_xy(r-2,a*6),
				*compute_xy(r+2,a*6),
				class_="thin",
			))

		pts = []

		(frac,whole) = modf(hp)
		frac = int(frac*100 + 0.5)

		for alt in frange(0, alt_max+0.01, 0.1):
			a = a_func(hp,alt)
			r = r_func(hp,alt)
			pts += compute_xy(r, a)

			if frac != 0 or hp == hp_max:
				continue
			if alt == alt_max:
				sz = 12
			elif alt in [35,45,55,65,75]:
				sz = 9
			else:
				continue
			g.append(draw.Text("%d" % (hp), sz,
				#*compute_xy(r,a),
				0, +8,
				class_="angle",
				transform="rotate(%.3f) translate(%.3f %.3f) rotate(-90)" % (a, r, 0),
			))
		if hp % 5 == 0:
			c = "thick"
		elif frac == 0:
			c = "thin"
		else:
			c = "extra_thin"

		g.append(draw.Lines(*pts, class_=c))


	sd_alt = degrees(acos(sd_coeff))

	for alt in [0,2,4,6,7,8,9,sd_alt] + frange(10, alt_max+1, 1):
		pts = []
		for hp in frange(hp_min, hp_max + 0.01, 0.1):
			a = a_func(hp,alt)
			r = r_func(hp,alt)
			pts += compute_xy(r, a)
		if alt == sd_alt:
			c = "red_thick"
		elif int(alt % 10) == 0:
			c = "extra_thick"
		elif int(alt % 5) == 0:
			c = "thick"
		else:
			c = "thin"
		path = draw.Lines(*pts, class_=c)
		g.append(path)

		if alt == sd_alt:
			g.append(draw.Text("Lunar semi-diameter", 10,
				path=path,
				text_anchor="middle",
				class_="red_angle",
				transform="translate(0 3)",
			))

		if int(alt % 10) != 0 or alt == 0:
			continue

		pts = []
		for hp in frange(hp_min+0.25, 61.5 + 0.01, 0.1):
			a = a_func(hp,alt)
			r = r_func(hp,alt)
			pts += compute_xy(r, a-0.5)
		path = draw.Lines(*pts)
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

	# draw some lines for the semi-diameter augmentation

	pts = []
	for alt in range(0,90+1):
		sd_aug = 0.3 * sin(radians(alt))
		(x,y) = compute_xy(offset + alt*0.9, -sd_aug*6)
		pts += (x,y)
		if alt % 10 != 0:
			continue
		g.append(draw.Lines(x, y-5, x, y+5, class_="thin"))
		g.append(draw.Text("%d" % (alt), 8,
			-y + 5,
			x+0,
			text_anchor="start",
			class_="red_angle",
			transform="rotate(-90)",
		))
	g.append(draw.Lines(*pts, class_="thin"))


	return g

####
#### Front side
####

def make_moon_front():
	front = draw.Group(transform="translate(500 500)")
	outer = draw.Group(id="outer", class_="spinner")
	inner = draw.Group(id="inner", class_="spinner")

	# Cut lines and axle
	inner.append(draw.Circle(0,0, cut, fill="white", stroke="none"))
	outer.append(draw.Circle(0,0, outer_cut, fill="white", stroke="none"))
	inner.append(draw.Circle(0,0, cut, class_="thick"))
	outer.append(draw.Circle(0,0, outer_cut, class_="thick"))
	inner.append(draw_axle())
	outer.append(draw_axle())

	inner.append(draw_marker("", cut, 180))

	inner.append(draw.Image(0, 0, 1000, 1000, path="spherical-triangle.svg", embed=True))


	# computing the lunar increments
	# do we still want this?
	#inner.append(make_moon(cut))
	#inner.append(make_fractional_minutes(cut-50, side=2, font_sz=10, max_angle=15, include_red=False, include_marker=True, divisions=60))

	inner.append(make_lunar_parallax(cut - 30))
	inner.append(make_fractional_minutes(cut, side=1, font_sz=12, max_angle=60, include_red=True, include_marker=True, divisions=10))

	outer.append(draw.Line(cut, 0, outer_cut, 0, class_="extra_thick"))
	outer.append(make_fractional_minutes(outer_cut, side=1, font_sz=10, include_red=True))
	outer.append(make_fractional_minutes(cut, side=2, font_sz=12, max_angle=60, include_red=True, include_marker=True))
	#outer.append(draw.Circle(0, 0, (outer_cut+cut)/2, class_="thin"))

	front.append(outer)
	front.append(inner)
	front.append(make_pointer("pointer"))

	return front

def make_moon_back():
	outer = draw.Group(id="back_outer", class_="spinner", transform="rotate(0)")
	inner = draw.Group(id="back_inner", class_="spinner", transform="rotate(0)")
	inner.append(draw.Circle(0,0, cut, fill="white", stroke="none"))
	outer.append(draw.Circle(0,0, outer_cut, fill="white", stroke="none"))
	inner.append(draw_axle())
	outer.append(draw_axle())
	inner.append(draw.Circle(0,0, cut, class_="thick"))
	outer.append(draw.Circle(0,0, outer_cut, class_="thick"))

	inner_offset = 100
	#inner.append(draw.Circle(0, 0, inner_offset, fill="black"))
	inner.append(make_lunar_parallax(cut, offset = cut - 120))
	inner.append(make_lunar_dist(cut-130, offset = cut - 300))
	inner.append(draw_marker("0", cut, 180))
	#inner.append(make_fractional_minutes(cut, side=1, max_angle=60, divisions=10, font_sz=10, include_marker=True))
	outer.append(make_fractional_minutes(cut, side=2, max_angle=60, divisions=10, font_sz=12, include_red=True, include_marker=True))
	outer.append(make_fractional_minutes(outer_cut, side=1, font_sz=10, include_red=True))
	outer.append(make_fractional_minutes(outer_cut - 50, side=2, max_angle=14+19/60, divisions=60, font_sz=12, include_red=False, include_marker=False))

	#outer.append(make_fractional_ccl(cut+25))
	#outer.append(make_fractional_ccl2(cut, outer_cut - cut))

	inner.append(draw.Image(-500, -500, 1000, 1000, path="lunar-triangle.svg", embed=True, transform="scale(0.8)"))
	return (inner,outer)


def make_moon_files():
	output_file = "moon.svg"

	d = draw.Drawing(2000,1000, origin=(0,0))
	d.append_css(css)
	a3 = draw_a3()

	front = make_moon_front()

	back = draw.Group(transform="translate(1500 500)")
	(inner,outer) = make_moon_back()
	back.append(outer)
	back.append(inner)
	back.append(make_pointer("back_pointer"))


	d.append(front)
	d.append(back)
	d.save_svg(output_file)


if __name__ == "__main__":
	make_moon_files()
