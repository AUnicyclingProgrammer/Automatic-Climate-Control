// Includes
include <BOSL2/std.scad>
include <BOSL2/threading.scad>
include <BOSL2/structs.scad>
include <BOSL2/hinges.scad>
include <BOSL2/screws.scad>
include <BOSL2/beziers.scad>

include <OU-OSL.scad>
/* 
// $fn to use for previewing
$preview_fn = 32;

// $fn to use when rendering
$render_fn = 90;

$fn = $preview ? $preview_fn : $render_fn; // Number of fragments used to draw a circle, first number is used for previewing, second is used for rendering
 */

    // Minimum angle to use when previewing
    $preview_fa = 4.0; //0.1

    // Minimum angle to use when rendering
    $render_fa = 2.0; //0.1

    $fa = $preview ? $preview_fa : $render_fa;

    // Minimum size (in mm) to use when previewing
    $preview_fs = 0.15; //0.01

    // Minimum size (in mm) to use when rending
    $render_fs = 0.10; //0.01

    $fs = $preview ? $preview_fs : $render_fs;


/*
Slop per layer height
0.2 standard quality printing: 0.2
0.32 fastRender prototyping: 0.4

$parent_size.x saving for later, super helpful
*/

$slop = 0.2; // mm, closest faces can be and still move a bit
scooch = 0.010; //0.001 //Just for making sure parts actually go together

/*
    Model of a B500K Potentiometer that I got from Mountain State Electronics

    Additional Part Info from back of unit:
    BI
    P160KN1D
*/

/*[Preview]*/

// ----- Parameters -----

/*[Body]*/

// Diameter of the body of the potentiometer
bodyDiameter = 16.5;

// Height of the body of the potentiometer (overall height, overly simplified)
bodyHeight = 9.4;

// Length of the positioning tab on the body
tabLength = 1.25;

// Width of the positioning tab on the body
tabWidth = 2.75;

// Height of positioning tab on body
tabHeight = 2.5;

tabDimensions = [tabLength, tabWidth, tabHeight];

// Rounding on the bottom of the body
bodyRounding = 1;

/*[Pins]*/

/*[Shaft]*/

/*[Knob]*/

/*[Misc.]*/
oversize = false;

// ----- Development -----

// ----- Constructing Assembly -----

BuildPotentiometer(oversizeForNegative = oversize) {
    // show_anchors(s = 2);
};

// ----- Modules and Functions -----
/*
    Build Potentiometer

    oversizeForNegative : if true, increases some dimensions by $slop so it can be used
        for making a negative
*/
module BuildPotentiometer(oversizeForNegative = false) {
    oversizeBy = oversizeForNegative ? get_slop() : 0;

    color_this("lightGrey")   
    intersection() {
        // Potentiometer
        zcyl(d = bodyDiameter + oversizeBy, h = bodyHeight + oversizeBy,
            rounding1 = bodyRounding) {
                color_this("lightGrey")   
                position(TOP+LEFT)
                cuboid(tabDimensions + oversizeBy*[2,2,1],
                    rounding = min(tabDimensions)/2, except = [TOP, BOT],
                    anchor = BOT+LEFT);

        };

        // Outline
        zcyl(d = bodyDiameter + oversizeBy, h = 2*(bodyHeight + oversizeBy));
    }
}


// ---------- Rendering Aids ----------

