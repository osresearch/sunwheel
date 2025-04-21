<!doctype html><meta charset=utf-8><title>shortest html5</title>
<body>
 Sextant specialized  slide rule

The main rule is used to help do the math on the minutes and seconds
of the measurement.

Adjusts observed altitude `H_o` into computed alitude `H_c` with:
* Height of eye above sea level
* Refraction as a function of latitude
* Upper or lower lim
* Declination of the sun


## Computing the observed height

Note that the rotating rings only measure minutes. You have
to do the math on the degrees separately.  If the pointer has crossed
the `0` on the outer ring, you need to keep track of the direction of
crossing and add or subtract one from the degrees at this point.

* If you don't already have it, measure the index error on the sextant by bringing the horizon down to itself and recording the minutes required to null out the error.
* Take a sun sight,  recording the uncorrected angle of the sextant (`H_s`) in degrees and minutes, as well as the height of eye `H_e` of the observation and which edge of the sun (upper or lower) is measured.
* Set the pointer on the outer ring for the minutes, seconds of the `H_s` and the inner ring at 0
* Rotate the pointer to the index error on the inner ring (positive or negative)
* Set the Height of Eye zero underneath the pointer
* Rotate the pointer to the correct height of eye to correct for dip. It now indicates the apparent altitude `H_a`
* Rotate the inner ring so that the upper or lower and the correct date range mark is under the pointer
* Rotate the pointer to the degrees of `H_s` on the refraction correction scale.
* The pointer now indicates on the outer ring the minutes and seconds of the corrected observed height `H_o`.
* Add or subtract 1 from the degrees and record the real `H_o`

## Computing latitude from a meridian passage

In the Sun Atlas, look up these three values for the current day of the year:

* GHA of the sun at noon GMT
* Declination of the sun at noon GMT
* `d` value, indicating how fast declination is changing per hour (in minutes)

Start with the blue pointer at the minutes and seconds `H_o` on the outer ring from before.  Then:

* Rotate the inner ring so that the minutes of the declination appears under the pointer

* Rotate the pointer so that the correct
* Compute the zenith distance: 90 - `H_o`.  The zenith distance minutes and seconds can be directly read from the red numbers on the outer ring.  The degrees can be read from the sine/cosine ring on the reverse side since it has 0-90 and 90-0 opposite each other.
* Rotate the inner ring so that noon on the `d` grid is under the pointer.
* Based on the GMT of the measurement, rotate the pointer so that it crosses
the correct part of the arc.
** Which part requires some thought (and this should be marked on the dial)
** Opposite hemispheres: subtract
** Same hemisphere, latitude > declination
** Same hemisphere, latitude < declination
* If d is positive, use the black times.  If d is negative, use the red times.
* TODO: add +/-d labels to the arc.
* Rotate the inner ring so that the zero is under the pointer
* Rotate the pointer to the minutes seconds of the declination on the inner
ring.
* TODO: fix this for the hemisphere cases
* The outer ring now has the minute seconds of the latitude.

## Worked example for latitude


<script>
var inner = 0;
var outer = 0;
var pointer = 0;
function set_rule(p,i,o) {
	var sliderule = document.getElementById("sliderule").contentDocument;

	// find the shortest way to rotate the inner one
	// the outer and pointer must take the long way around
	if (i - inner > 30)
		i = i - 60;
	else
	if (i - inner < -30)
		i = i + 60;

	inner = i;
	outer = o;
	pointer = p;
	sliderule.getElementById("pointer").style.transitionDuration = '2s';
	sliderule.getElementById("inner").style.transitionDuration = '2s';
	sliderule.getElementById("outer").style.transitionDuration = '2s';
	sliderule.getElementById("inner").setAttribute("transform","rotate(" + -i*6 + ")");
	sliderule.getElementById("outer").setAttribute("transform","rotate(" + -o*6 + ")");
	sliderule.getElementById("pointer").setAttribute("transform","rotate(" + p*6 + ")");
}
set_rule(0,0,0);
</script>

<table>
<tr>
<td width="60%"><object id="sliderule" data="rule.svg" width="100%"></object></td>
<td>
<pre>
2025-04-21 @ 20:21 UTC 10C normal pressure
`IC` = +0.2' index error
`H_s` = 35 deg 3.4' lower limb, facing south 
`H_e` = 6m above sea level
Declination at noon N12 deg 02.4' d=+0.8
</pre>
Correcting sextant height measurement:
<ul>
<li onclick="set_rule(0,0,0)">Start with the pointer on the inner and outer at 0
<li onclick="set_rule(0,0,3.4)">Rotate the outer dial to the minutes of the sextant height, 3.4'.
<li onclick="set_rule(0.2,0,3.4)">Point to the index error 0.2 on the inner dial, read the corrected height of 3.6'.
<li onclick="set_rule(0.0,37.6,3.6)"> Rotate the inner dial so that the 6m height of eye is under the pointer.
<li onclick="set_rule(-5.8,37.6,3.6)">
Rotate the pointer so that it lines up with the current temperature and height of the measurement (10C and 34&deg;).
<li onclick="set_rule(0.0,37.6-5.8,-2.2)">
Note that this has rotated *past* the zero mark on the outer dial, so we need to subtract one from
our measurement.  The height corrected for the dip and refraction is now 34&deg; 57.8'.

<li onclick="set_rule(0.0,-16.0,-2.2)">
Rotate the pointer so that the lower limb and approximate current date (midway through April in this example) is under the pointer. This corresponds to a semi diameter of 16.0'.
<li onclick="set_rule(16.0, -16.0, -2.2)">Set the pointer to the zero on the inside scale and note that the it passed the zero mark on the outside scale in the positive direction, so we need to add one to the degree value.
<li onclick="set_rule(0.0, 0, 13.8)">Now the correct adjusted sextant height is <b>35&deg; 13.8'</b> after compensating for dip, refraction, temperature, sun semidiameter and the lower limb measurement.
</ul>
Computing latitude (same hemisphere, L > D):
<ul>
<li onclick="set_rule(0.0,2.4,13.8)"/>L > D, so L=90-(H-D), which means subtracting the sun declination from the sextant height.  Rotate the inner dial so that 2.4 in black lines up with the pointer, which will move the noon value higher.
<li onclick="set_rule(-6.7-2.4,2.4,13.8)"/>d is positive and we are subtracting the declination change. Rotate the pointer to where the 0.8 line intersects the 21:21 with the red numbers.
<li onclick="set_rule(0,-6.7, 4.7)"/>Read the minutes off the black numbers on the outer dial and compute the H-D value as 35&deg; 4.7m - 12&deg; = 23&deg; 4.7' (the minutes of declination have already been handled).
<li>Compute the latitude as 90 - 23&deg; 4.7'. 60' - 4.7' can be read from the red numbers on the outer scale, while the sine/cosine scale on the reverse can be used to estimate the degrees 90-23 = 66 point something.  The result is <b>66&deg; 55.3'</b>.
</ul>
</tr>
</table>




