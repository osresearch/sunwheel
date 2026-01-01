/* Printed cursor for the paper sliderule.
 * It is double sided and has space for a red thread
 * to act as the center cursor.
 */

len = 85;
shaft = 2.25;
paper_thick = 2.4;
thick = 10/2;
thread_hole = 1.5;

astrolabe_thick = 5;
astrolabe_width = 6;
astrolabe_arm_offset = len/2 - 8;
astrolabe_arm_width = 8;

nut = true;
pin_slop = 0.3;

module bolt(nut)
{
	// either a counter sink or a nut
	if (nut)
		rotate([0,0,30]) cylinder(d=5.0, h=2, $fn=6);
	else {
		cylinder(d2=shaft, d1=shaft+3, h=1.5, $fn=90);
		translate([0,0,-5]) cylinder(d=shaft+3, h=5, $fn=90);
	}
	cylinder(d=shaft, h=10, $fn=30);
}

module cursor(nut)
{
render() difference()
{
	union() {
		hull() {
			scale([0.5,1,1]) cylinder(d=20, h=thick, $fn=180);
			translate([len,0,0]) cylinder(d=15, h=thick, $fn=180);
		}

		// peg on the end
		translate([len+5,2,thick]) cylinder(d1=shaft, d2=shaft-pin_slop, h=thick/2 - pin_slop, $fn=30);
	}

	// peg hole on the end
	translate([len+5,-2,thick/2]) cylinder(d=shaft+pin_slop, h=thick, $fn=30);

	// thread hole and slot on the outside
	translate([len+2,0,-1]) cylinder(d=thread_hole, h=thick+2, $fn=30);
	translate([len-5/2-0.5,-1/4,thick-paper_thick/2-0.75]) cube([5,1/2,3.5]);

	// thread hole and slot on the inside
	translate([5.5,0,-1]) cylinder(d=thread_hole, h=thick+2, $fn=30);
	translate([5.5,-1/4,thick-paper_thick/2-0.75]) cube([5,1/2,1.5]);

	// m2.5 shaft in the middle
	bolt(nut);
/*
	translate([0,0,-1]) cylinder(d=shaft, h=thick+2, $fn=90);

	// either a counter sink or a nut
	%cylinder(d=5, h=10, $fn=30);
	if (nut)
		rotate([0,0,30]) cylinder(d=shaft+4.0, h=2, $fn=6);
	else
		cylinder(d2=shaft, d1=shaft+3, h=1.5, $fn=90);
*/

	// space for the inside parts
	translate([0,0,thick-paper_thick/2]) cylinder(r=len+1, h=thick, $fn=180);

	// cut out for the viewing window
	//translate([5,-12.5/2,-1]) cube([len-5,12.5,thick*2]);

	hull() {
		translate([11,0,-1])
scale([0.5,1,1]) cylinder(d=14,h=thick*2, $fn=90);
		translate([len-2,0,-1])
scale([0.5,1,1]) cylinder(d=11,h=thick*2, $fn=90);
	}
}
}


/* Two part cursor for the astrolabe side.
 * This mates with the normal cursor, but has a swing out arm
 * called a "brachiolus" to point to a specific declination
 * and local hour angle, which can then be rotated independently
 * of the face to translate to a height and bearing.
 */
module astrolabe_cursor(nut)
{
render() difference()
{
	union() {
		hull() {
			cylinder(d=astrolabe_width, h=astrolabe_thick, $fn=180);

			translate([len,0,0]) cylinder(d=astrolabe_width, h=astrolabe_thick, $fn=180);

		}

		// hinge piece for the arm
		translate([astrolabe_arm_offset,astrolabe_width/2,0])
		cylinder(d=astrolabe_arm_width, h=astrolabe_thick/2, $fn=180);

		// matching piece for the other side
		translate([len,0,0]) cylinder(d=15, h=astrolabe_thick + paper_thick/2, $fn=180);

		// peg on the end to match the other side
		translate([len+5,2,astrolabe_thick+paper_thick/2]) cylinder(d1=shaft, d2=shaft-pin_slop, h=thick/2 - pin_slop, $fn=30);
	}

	// peg hole on the end for the other side
	translate([len+5,-2,thick/2])
	cylinder(d=shaft+pin_slop, h=thick, $fn=30);

	// counter sink, with 1mm of extra clearance
	translate([0,0,1]) bolt(nut);

	// space for the inside sheets of the slide rule
	translate([0,0,astrolabe_thick]) cylinder(r=len+1, h=thick, $fn=180);

	// M2x6 screw for the rotating arm (not counter sunk)
	translate([astrolabe_arm_offset,astrolabe_width/2,-0.1])
	cylinder(d=shaft, h=10, $fn=30);

	// opposide hinge piece for the arm
	translate([astrolabe_arm_offset,astrolabe_width/2,astrolabe_thick/2]) cylinder(d=astrolabe_arm_width, h=astrolabe_thick/2, $fn=180);

	// and clearance for the arm in the opposite position
	translate([astrolabe_arm_offset,astrolabe_width/2,astrolabe_thick/2])
	rotate([0,0,180-4])
	cube([astrolabe_arm_offset+5, astrolabe_width/2, astrolabe_thick/2]);
}
}


// The swing arm
module astrolabe_arm()
{
	render() difference()
	{
		union() {
			cylinder(d=astrolabe_arm_width-0.2, h=astrolabe_thick/2, $fn=90);
			translate([0,-astrolabe_width/2, 0])
			cube([len - astrolabe_arm_offset, astrolabe_width/2, astrolabe_thick/2]);
		}

		bolt(true);

		// cutout for the disc at the end of the arm
		translate([len - astrolabe_arm_offset-0.5,astrolabe_width/2,-1]) cylinder(d=15, h=thick, $fn=90);

		// ramp it down to a point
		translate([len-astrolabe_arm_offset-5,10/2,0])
		rotate([0,30-180,0])
		rotate([180,0,0])
		cube([20, 10, 10]);
		

		// and a finger notch to make it easier to pry
		translate([len/3,+0.1,astrolabe_thick-0])
		rotate([90,0,0])
		scale([1.25,1,1])
		cylinder(d=8, h=astrolabe_width/4, $fn=60);
	}
}


if(1)
{
%translate([0,35,0])
cursor(true);

//rotate([0,0,180])
astrolabe_cursor(false);


//rotate([180,0,0])
translate([astrolabe_arm_offset,-astrolabe_width/2-10,0])
astrolabe_arm();

} else {

	// printable
	astrolabe_cursor(false);
	//translate([0,20,0]) slider();
}
