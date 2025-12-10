/* Printed cursor for the paper sliderule.
 * It is double sided and has space for a red thread
 * to act as the center cursor.
 */

len = 85;
shaft = 2.5;
paper_thick = 2.4;
thick = 10/2;
thread_hole = 1.5;

nut = true;
pin_slop = 0.3;


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
	translate([0,0,-1]) cylinder(d=shaft, h=thick+2, $fn=90);

	// either a counter sink or a nut
	%cylinder(d=5, h=10, $fn=30);
	if (nut)
		rotate([0,0,30]) cylinder(d=shaft+4.0, h=2, $fn=6);
	else
		cylinder(d2=shaft, d1=shaft+3, h=1.5, $fn=90);

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

cursor(true);
translate([len,25,0])
rotate([0,0,180])
cursor(false);
