
var limb = 'upper';
var inner;
var outer;
var pointer;
var sliderule;
var speed = "2s";
var computed = 0;
var computed_min = 0;
var computed_deg = 0;
var za = 0;

var index_error = -0.2;
var temperature = 10;
var height_deg = 35;
function get(id) { return Number(document.getElementById(id).value) }
function set(id,v) {
	var elem = document.getElementById(id);
	if (elem)
		elem.innerHTML = v;
}

var height_of_eye_offset = -180 / 6;

function height_of_eye(H_e) {
	return (1.76 * Math.sqrt(H_e));
}

function radians(deg)
{
	return Math.PI * deg / 180;
}


function refraction(H_a, p=1010, t=10)
{
        let r = 1/Math.tan(radians(H_a + 7.31 / (H_a + 4.4)))
        let f = p / (273+t) * 283/1010
        return f * r;
}

function compute_refraction_and_height()
{
	let ha = get("height_deg"); // should use fraction too
	let t = get("temperature");
	return refraction(ha, 1010, t) + height_of_eye(get("eye_height"));
}

function semi_diam()
{
	let time = document.getElementById("date").value;
	let mon = Number(time.substr(5,2));
	let day = Number(time.substr(8,2));
	let approx = [
 		16.29, // Jan"],
                16.26, // Feb
                16.17, // Mar
                16.03, // Apr"],
                15.90, // May
                15.80, // Jun
                15.75, // Jul"],
                15.78, // Aug"],
                15.87, // "],
                16.00, // Oct"],
                16.14, // "],
                16.24, // Dec"],
 		16.29, // Jan"],
	];

	return (approx[mon-1] * day + approx[mon] * (31-day)) / 31
}

function compute_limb(step)
{
	if (limb == "star")
		return 0; // never any correction
	if (limb == "lower")
	{
		if (step == 1)
			return 0;
		return +semi_diam()
	}

	// upper always goes the same way
	return -semi_diam()
}

function degrees(d) { return d * 180 / Math.PI }
function radians(d) { return d * Math.PI / 180 }

function get_date()
{
	let time = document.getElementById("date").value;
	let mon = Number(time.substr(5,2));
	let day = Number(time.substr(8,2));
	let d = 30 * (mon-1) + (day+0.5); // approximately at noon
	return d;
}

function get_declination()
{
	return declination(get_date());
}

function declination(d)
{
        return -degrees(Math.asin(0.39779 * Math.cos(radians(0.98565 * (d+10) + 1.914 * Math.sin(radians(0.98565 * (d-2)))))))

}

function rotate(elem, value, speed)
{
	elem.value = value;
	elem.style.transform = "rotate(" + -value*6 + "deg)";
}

function setup(){
	var date = document.getElementById("date");
	if (date.value == "")
		date.valueAsDate = new Date();
	sliderule = document.getElementById("sliderule").contentDocument;
	pointer = sliderule.getElementById("pointer");
	inner = sliderule.getElementById("inner");
	outer = sliderule.getElementById("outer");

	set("ho", "");
	set("za", "");
	set("decl", "");
	set("lat", "");
	set("log", "");

	rotate(pointer, 0, speed)
	rotate(inner, 0, speed)
	rotate(outer, 0, speed)
	step = 0;
}

window.onload = setup;

function reset_pointer(all=0)
{
	// rotate so that the pointer is level and the outer
	// marks the current pointed to value
	rotate(outer, outer.value - pointer.value, speed)
	if (all)
		rotate(inner, inner.value - pointer.value, speed)
	rotate(pointer, 0, speed)

}

function set_rule(p,i,o) {
	sliderule = document.getElementById("sliderule").contentDocument;

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
	sliderule.getElementById("pointer").style.transitionDuration = speed;
	sliderule.getElementById("inner").style.transitionDuration = speed;
	sliderule.getElementById("outer").setAttribute("transform","rotate(" + -outer*6 + ")");
	sliderule.getElementById("pointer").setAttribute("transform","rotate(" + pointer*6 + ")");
}

function move_rule(which, value, rel=0)
{
	var elem = sliderule.getElementById(which);

	if (rel)
		value += elem.value;
	rotate(elem, value);
}
//set_rule(0,0,0);


function fmt_min(min, color=1)
{
	var s = min.toFixed(1) + "'"
	if (color)
		s = recolor(min, s)
	return s;
}

function fmt_deg(deg, color=1)
{
	var s = deg.toString() + "&deg;"
	if (color)
		s = recolor(deg, s);
	return s;
}

function fmt(deg,color=1)
{
	if (-1 < deg && deg < 0)
	{
		// special case for -0 degrees
		var s = "-0&deg;" + fmt_min(-deg*60, 0);
		if (color)
			s = recolor(deg, s);
		return s;
	}

	var min = (deg % 1) * 60;
	deg = Math.trunc(deg);

	if (min < 0)
		min = -min;

	var s = deg.toString() + "&deg;" + fmt_min(min, 0);
	if (color)
		s = recolor(deg, s);
	return s;
}

function next_step()
{
	if (step >= steps.length)
		step = 0;

	console.log("step=", step)
	var desc_elem = document.getElementById("log");
	var li = document.createElement('li');
	li.innerHTML = steps[step++]()
	desc_elem.appendChild(li)
}

function bold(s) { return "<b>" + s + "</b>" }
function recolor(sign,s) {
	return '<span class=' +
		(sign < 0 ? "negative" : "positive" ) +
		'>' + s + '</span>';
}

var steps = [
() => {
	var h = get('height_min')
	move_rule('outer', h);
	return "Rotate the outer dial black digits to the minutes of the sextant altitude: " + fmt_min(h);
},
() => {
	var ic = get('index_error')
	move_rule('pointer',ic);
	return  "Point to the sextant index error on the inner dial red digits: " + fmt_min(ic);
},
() => {
	reset_pointer(1);
	//move_rule('inner', -get('index_error'))
	var ha = get('height_deg') + outer.value/60;
	return "Read the apparent altitude from the outer dial black digits: " + recolor(ha, "Ha = " + fmt(ha));
},
() => {
	reset_pointer();
	var he = get('eye_height');
	var eye_correction = height_of_eye(he);
	move_rule('inner',eye_correction-height_of_eye_offset);

	return "Rotate the inner dial so that the height of eye is under the pointer: " + recolor(he, he.toFixed(1) + "m");
},
() => {
	var refraction = compute_refraction_and_height();

	move_rule('pointer', refraction , 1);
	return "Rotate the pointer so that it lines up with the current temperature and original sextant altitude."
},
() => {
	reset_pointer(1);
	var h = get('height_deg') + outer.value / 60;
	return "Read the refraction and temperature corrected height measurement from the outer ring: " + fmt(h);
},
() => {
	if (limb == "star") {
		move_rule('inner', 0);
		step += 1; // skip the next one
		return "Since this is a star measurement, no limb correction is necessary";
	}

	var diam = semi_diam();

	if (limb == "upper") {
		move_rule('inner', -diam);
		return "Upper limb measurements moves the inner ring to line up with the semi diameter for the date " + fmt_min(diam);
	} else {
		move_rule('inner', 0);
		return "Lower limb measument moves the the inner ring to zero";
	}
},
() => {
	var diam = semi_diam();

	if (limb == "upper") {
		move_rule('pointer', -diam);
		return "Upper limb measurement moves the pointer to zero on the inner ring (adding semi diameter to the height)";
	} else {
		move_rule('pointer', +diam);
		return "Lower limb measurement moves the pointer to approximate date (subtracting semi diameter from the height) " + fmt_min(diam);
	}
},
() => {
	reset_pointer(1);

	// store the computed height
	computed_deg = get('height_deg');
	computed_min = outer.value;
	computed = computed_deg + computed_min / 60;

	var s = recolor(computed, "Ho = " + fmt(computed, 0));
	set("ho", s);

	return "Finally, read the corrected observed height measurement minutes from the outer ring: " + s;
},
() => {
	move_rule('outer', 0);
	var s = "To compute the Zenith Angle, which is the signed compliment of the observed height, reset the outer and rotate the pointer to ";

	var dir = get('direction') - 0.5;

	if (dir > 0)
	{
		move_rule('pointer', 90 - computed);
		return s + "Ho on the black of the outer outer ring " + fmt(computed) + " (since we are north of the Sun)";
	} else {
		move_rule('pointer', computed - 90);
		return s + "set Ho on the red of the outer outer ring " + fmt(-computed) + " (since we are south of the Sun)";
	}
},
() => {
	reset_pointer(1);
	za = -outer.value;
	set("za", recolor(za, "Za = " + fmt(za)));

	var s = "Read the Zenith Angle " + fmt(za) + " from the opposite color on the outer ring.";
	s += " Note that the minutes are " + fmt_min((za % 1) * 60) + " = 60 - " + fmt_min(computed_min);
	s += "<br/>Zenith angles are positive north of the sun, negative south of the sun."
	s += "<hr/>"
	return s;
},
() => {
	var decl = get_declination();
	var hemi = decl > 0 ? 'Northern' : 'Southern';
	
	move_rule('pointer', 0);
	move_rule('inner', decl);

	set("decl", recolor(decl, "Decl = " + fmt(decl)) + " (approx)");

	return "For an approximate latitude, approximate the Sun's declination by rotate the inner to align the analemma date with the pointer and read the angle on the inner ring "+ fmt(decl) + " (" + hemi + " hemisphere)";
},
/*
() => {
	var dir = get('direction') - 0.5;
	var which = dir > 0 ? "black" : "red"

	move_rule('pointer', outer.value + (dir > 0 ? 90-computed : computed - 90));

	return "To compute the lattitude requires the Zenith angle, 90 - Ho. Set the pointer to Ho on the " + which + " outer outer ring (since the sight is facing " + (dir > 0 ? "north" : "south") + ")";
},
() => {
	reset_pointer(1);
	var dir = get('direction') - 0.5;
	var which = dir > 0 ? "red" : "black"
	return "Read the approximate zenith angle from the " + which + "outer ring Z = " + fmt(-outer.value) + " (note that the sign flips and that the minutes are 60 - " + fmt_min(computed_min) + " minutes)";
},
*/
() => {
	move_rule('pointer', outer.value);
	reset_pointer(1)
	var lat = inner.value;
	set("lat", recolor(lat, "Lat = " + fmt(lat)) + " (approx)");
	return "Since the Zenith angle was already set on the outer, move the pointer to the outer origin and read the approximate latitude in degrees from the inner ring " + fmt(lat) + "<hr/>";
},
() => {
	var date = get_date();
	var decl = declination(date);
	var d = (declination(date + 1.0/24) - decl) * 60;

	var date = document.getElementById("date").value;
	let mon = date.substr(5,5);
	var ts = date.substr(11,5)
	var hour = Number(ts.substr(0,2))
	var min = Number(ts.substr(3,2))
	hour = hour + min / 60 - 12;
	
	var s = "For a more accurate latitude, consult the alamanc for the current date. It might look something like<br/><tt>" + mon + " " +  fmt(decl,0) + " " + fmt_min(d,0) + " " + "-3:30" + "</tt><br/>";

	var decl_min = (decl % 1) * 60;

	move_rule('inner', 0);
	move_rule('pointer', 0);
	move_rule('outer', decl_min);
	return  s + "The alamanc's declination of the sun at noon GMT is " + fmt(decl) + ". Set the minutes " + fmt_min(decl_min) + " on the outer ring.";
},
() => {
	var date = get_date();
	var decl = declination(date);
	var d = (declination(date + 1.0/24) - decl) * 60;

	var date = document.getElementById("date").value;
	let mon = date.substr(5,5);
	var ts = date.substr(11,5)
	var hour = Number(ts.substr(0,2))
	var min = Number(ts.substr(3,2))
	hour = hour + min / 60 - 12;

	move_rule('pointer', -hour*d);

	return "The alamanc d value is " + fmt_min(d) + " which means that the declination changes that many minutes per hour. To compute the declination at time of measurement, set pointer to " + recolor(d,ts) + " (use the " + (d < 0 ? "red" : "black") + " times to match the sign on d)";

},
() => {
	var decl = get_declination();
	reset_pointer(1);
	//decl = outer.value / 60;

	var decl_min = outer.value;
	computed_decl = Math.trunc(decl) + decl_min/60
	set("decl", recolor(computed_decl, "Decl = " + fmt(computed_decl)));

	return "Read the corrected minutes from the outer " + fmt_min(decl_min) + " and compute the actual declination " + fmt(computed_decl);
},
() => {
	move_rule('inner', 0);
	return "Reset the inner";
},
() => {
	var za_min = (za % 1) * 60
	move_rule('pointer', -za_min);
	return "Set the pointer to the Zenith Angle minutes " + fmt_min(za_min);
},
() => {
	reset_pointer(1);
	var decl = get_declination();
	var min = outer.value;
	var lat = Math.trunc(decl) + Math.trunc(za) + min/60;

	set("lat", recolor(lat, "Lat = " + fmt(lat)));

	var s = "Read the computed minutes of lattitude from the outer ring " + fmt_min(min);
	s += "<br/>And compute L = D + Za = " + fmt_deg(Math.trunc(decl)) + " + " + fmt_deg(Math.trunc(za)) + " + " + fmt_min(min) + " = " + fmt(lat);
	return s;
},

];

