# Sextant specialized  slide rule

The main rule is used to help do the math on the minutes and seconds
of the measurement.

Adjusts observed altitude `H_o` into computed alitude `H_c` with:
* Height of eye above sea level
* Refraction as a function of latitude
* Upper or lower lim
* Declination of the sun


## Computing the observed height

Note that the rotating rings only measure minutes and seconds. You have
to do the math on the degrees separately.  If the pointer has crossed
the `0` on the outer ring, you need to keep track of the direction of
crossing and add or subtract one from the degrees at this point.

* If you don't already have it, measure the index error on the sextant by bringing the horizon down to itself and recording the minutes seconds required to null out the error.
* Take a sun sight,  recording the uncorrected angle of the sextant (`H_s`) in degrees, minutes, seconds, as well as the height of eye `H_e` of the observation and which edge of the sun (upper or lower) is measured.
* Set the pointer on the outer ring for the minutes, seconds of the `H_s` and the inner ring at 0
* Rotate the pointer to the index error on the inner ring (positive or negative)
* Set the Height of Eye zero underneath the pointer
* Rotate the pointer to the correct height of eye to correct for dip. It now indicates the apparent altitude `H_a`
* Rotate the inner ring so that the upper or lower and the correct date range mark is under the pointer
* Rotate the pointer to the degrees of `H_s` on the refraction correction scale.
* The pointer now indicates on the outer ring the minutes and seconds of the corrected observed height `H_o`.
* Add or subtract 1 from the degrees and record the real `H_o`

## Computing latitude from a meridian passaeg

Look up the declination of the sun in the atlas for noon GMT and the `d` value
that indicates how fast it is changing.  

* Start with the blue pointer at the minutes and seconds `H_o` on the outer ring from before.
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
