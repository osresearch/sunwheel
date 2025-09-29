
var limb = 'upper';
var inner;
var outer;
var pointer;
var sliderule;
var speed = "2s";
var computed = 0;
var computed_min = 0;
var computed_deg = 0;

var index_error = -0.2;
var temperature = 10;
var height_deg = 35;
function get(id) { return Number(document.getElementById(id).value) }

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
	document.getElementById("date").valueAsDate = new Date();
	sliderule = document.getElementById("sliderule").contentDocument;
	pointer = sliderule.getElementById("pointer");
	inner = sliderule.getElementById("inner");
	outer = sliderule.getElementById("outer");

	rotate(pointer, 0, speed)
	rotate(inner, 0, speed)
	rotate(outer, 0, speed)
	step = 0;

	document.getElementById("log").innerHTML = "";
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


function fmt(min,deg=0,prec=1)
{
	var rc = ''
	if (min < 0)
	{
		min += 60;

		if (deg == 0) {
			rc = '-';
		} else {
			deg -= 1;
		}
	}

	if (min > 60)
	{
		deg += 1
		min -= 60;
	}

	if (deg != 0)
	{
		rc += deg + "°"
		if (min < 10)
			rc += '0'
	}

	rc += min.toFixed(prec) + "'"
	return "<b>" + rc + "</b>";
}

function next_step()
{
	if (step == 0)
		setup();

	if (++step >= steps.length)
		step = 0;

	console.log("step=", step)
	var desc_elem = document.getElementById("log");
	var li = document.createElement('li');
	li.innerHTML = steps[step]()
	desc_elem.appendChild(li)
}

var step = 0;
var steps = [
() => {
	setup();
	return "Start with the pointer on the inner and outer ring at 0";
},
() => {
	var h = get('height_min')
	move_rule('outer', h);
	return "Rotate the outer dial black digits to the minutes of the sextant altitude: " + fmt(outer.value);
},
() => {
	var ic = get('index_error')
	move_rule('pointer',ic);
	return  "Point to the sextant index error on the inner dial red digits: " + fmt(ic);
},
() => {
	reset_pointer();
	move_rule('inner', -get('index_error'))
	return "read the observed altitude from the outer dial black digits: " + fmt(outer.value, get('height_deg'));

},
() => {
	reset_pointer();
	var he = get('eye_height');
	var eye_correction = height_of_eye(he);
	move_rule('inner',eye_correction-height_of_eye_offset);

	return "Rotate the inner dial so that the height of eye is under the pointer: " + he.toFixed(1) + "m";
},
() => {
	var refraction = compute_refraction_and_height();

	move_rule('pointer', refraction , 1);
	return "Rotate the pointer so that it lines up with the current temperature and original sextant altitude."
},
() => {
	reset_pointer(1);
	return "Read the refraction and temperature corrected height measurement from the outer ring: " + fmt(outer.value, get('height_deg'));
},
() => {
	if (limb == "star") {
		move_rule('inner', 0);
		step += 1; // skip the next one
		return "Since this is a star measurement, no limb correction is necessary";
	}
	if (limb == "upper") {
		move_rule('inner', -semi_diam());
		return "Upper limb measurements moves the inner ring to line up with the semi diameter for the date " + fmt(semi_diam(), 0);
	} else {
		move_rule('inner', 0);
		return "Lower limb measument moves the the inner ring to zero";
	}
},
() => {
	if (limb == "upper") {
		move_rule('pointer', -semi_diam());
		return "Upper limb measurement moves the pointer to zero on the inner ring (adding semi diameter to the height)";
	} else {
		move_rule('pointer', +semi_diam());
		return "Lower limb measurement moves the pointer to approximate date (subtracting semi diameter from the height) " + fmt(semi_diam(), 0);
	}
},
() => {
	reset_pointer(1);

	// store the computed height
	computed_deg = get('height_deg');
	computed_min = outer.value;
	computed = computed_deg + computed_min / 60;

	return "Finally, read the corrected height measurement minutes from the outer ring: " + fmt(computed_min, computed_deg);
},
() => {

	move_rule('outer', 0);
	return "To compute the approximate lattitude, return the outer ring to zero";
},
() => {
	var decl = get_declination();
	var min = (decl % 1)*60;
	var deg = Math.trunc(decl);
	var hemi = 'Northern';
	if (min < 0)
	{
		hemi = 'Southern';
		min = -min;
	}
	
	move_rule('inner', decl);
	return "Rotate the inner to align the analemma date to find the declination of the sun "+ fmt(min, deg, 0) + " in the " + hemi + " hemisphere";
},
() => {
	var decl = get_declination();
	var dir = get('direction') - 0.5;

	if (dir > 0)
	{
		move_rule('pointer', 90 - computed);
		return "Looking north, L = D + H - 90. Set the pointer to computed height on the outer outer black " + fmt(computed_min, computed_deg);
	} else {
		move_rule('pointer', computed - 90);
		return "Looking south, L = D + (90 - h). Set the pointer to the computed height on the outer outer red " + fmt(computed_min, computed_deg);
	}
},
() => {
	reset_pointer(1)
	var lat_min = Math.abs((inner.value % 1) * 60);
	var lat_deg = Math.trunc(inner.value);
	return "Read the approximate latitude in degrees from the inner ring " + fmt(lat_min, lat_deg);
},
() => {
	move_rule('inner', 0);
	move_rule('pointer', 0);
	move_rule('outer', 0);

	return "To compute exact latitude for meridan site requires the almanac. Reset all the rings"; //, leave the outer on the observed minutes height " + fmt(computed_min, computed_deg);
},
() => {
	var date = get_date();
	var decl = declination(date);
	var d = (declination(date + 1.0/24) - decl) * 60;
	
	var decl_min = (decl % 1) * 60;
	move_rule('outer', decl_min);

	return "Assuming the declination is " + decl.toFixed(2) + ", set the inner to point to the minutes on the outer " + decl_min.toFixed(1);
},
() => {
	// todo -- reverse the order of these so the value is on inner ring
	var date = get_date();
	var decl = declination(date);
	var d = (declination(date + 1.0/24) - decl) * 60;

	var date = document.getElementById("date").value;
	var hour = Number(date.substr(11,2));
	var min = Number(date.substr(14,2));
	hour = hour + min / 60 - 12;
	
	move_rule('pointer', -hour * d);
	return "Assuming the d is " + d.toFixed(1) + ". Set pointer to current time " + hour.toFixed(2) + " (GMT)";
},
() => {
	var decl = get_declination();
	reset_pointer(1);
	//decl = outer.value / 60;

	return "Read the corrected minutes from the outer " + outer.value.toFixed(1) + " and compute declination " + (outer.value/60 + Math.trunc(decl)).toFixed(2);
},
];
