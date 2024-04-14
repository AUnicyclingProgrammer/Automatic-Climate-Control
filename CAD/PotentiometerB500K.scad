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

/*[PCB and Pins]*/

// Length of the PCB (spans the pins)
pcbLength = 15.5;

// Width of the PCB (spans to the far side of the potentiometer)
pcbWidth = 20.25;

// Thickness of the PCB (includes the pins just to be safe)
pcbHeight = 2;

pcbDimensions = [pcbLength, pcbWidth, pcbHeight];

// Distance the bottom of the PCB is from the bottom of the body
pcbPlacementHeight = 5.75;

// Width of each pin
pinWidth = 1;

// Length of each pin
pinLength = 5;

// Thickness of each pin
pinHeight = 1.25;

pinDimensions = [pinWidth, pinLength, pinHeight];

// The width of the pin material that overlaps with the PCB
pinOverlapWidth = 3.75;

// The amount of the pins overlap with the PCB
pinOverlapLength = 4.5;

// Thickness of the pin material that overlaps with the PCB
pinOverlapHeight = 0.5;

pinOverlapDimensions = [pinOverlapWidth, pinOverlapLength, pinOverlapHeight];

/*[Shaft]*/

// Diameter of the threaded shaft (threads included, thus it's the nominal diameter)
shaftDiameter = 6.8;

// Height of the threaded part of the shaft
shaftHeight = 6.5;

/*[Knob]*/

/*[Misc.]*/
$metalColor = "lightGrey";
$pcbColor = "peru";

oversize = false;

// ----- Global Variables -----

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
module BuildPotentiometer(oversizeForNegative = false,
    anchor = CENTER, spin = 0, orient = UP) {

    oversizeBy = oversizeForNegative ? get_slop() : 0;

    _BuildBody(oversizeBy) {
        show_anchors(s = 3);

        // PCB and pins
        position(BOT)
        up(pcbPlacementHeight)
        _BuildPCBandPins(oversizeBy, anchor = BOT);

        // Shaft
        position(TOP)
        _BuildShaft(oversizeBy, anchor = BOT) {

        };
    };
}

/*
    Builds the threaded shaft

    oversizeBy : the amount the part should be oversized by
*/
module _BuildShaft(oversizeBy,
    anchor = CENTER, spin = 0, orient = UP) {
    color_this($metalColor)
    if (approx(oversizeBy,0)) {
        threaded_rod(h = shaftHeight, d = shaftDiameter, pitch = 0.5,
            anchor = anchor, spin = spin, orient = orient);
    } else {
        zcyl(h = shaftHeight, d = shaftDiameter + 2*oversizeBy,
            anchor = anchor, spin = spin, orient = orient);
    }
}
/*
    Builds the PCB and the pins

    oversizeBy : the amount the part should be oversized by
*/
module _BuildPCBandPins(oversizeBy,
    anchor = CENTER, spin = 0, orient = UP) {
    
    // Key values
    potentiometerDiameter = bodyDiameter + 2*oversizeBy;

    pcbCuboidDimensions = pcbDimensions + oversizeBy*[2,2,2]
        -[0,potentiometerDiameter/2,0];

    // Building PCB
    union() {
        // Part that goes through potentiometer body
        color_this($pcbColor)
        zcyl(d = potentiometerDiameter, h = pcbCuboidDimensions.z) {
            // PCB
            color_this($pcbColor)
            position(CENTER)
            cuboid(pcbCuboidDimensions, anchor = BACK) {
                if (approx(oversizeBy, 0)) {
                    // Pins
                    position(BOT+FRONT)
                    xcopies(n = 3, spacing = 0.2*INCH)
                    _BuildPin(anchor = BACK+TOP);
                } else {
                    // Making space for pins
                    position(BOT+FRONT)
                    back(pinOverlapDimensions.y)
                    cuboid([pcbCuboidDimensions.x,
                        pinDimensions.y + pinOverlapDimensions.y,
                        pinDimensions.z]
                        + get_slop()*[0,2,2],
                        anchor = BACK+TOP
                    );

                    // "Extending" PCB
                    position(FRONT)
                    cuboid([pcbCuboidDimensions.x,
                        pinDimensions.y + 2*get_slop(),
                        pcbCuboidDimensions.z],
                        anchor = BACK);
                }
            };
        };
    }
}

/*
    Builds a singular pin
*/
module _BuildPin(anchor = CENTER, spin = 0, orient = UP) {
    color_this($metalColor)
    union() {
        // Pin
        cuboid(pinDimensions, chamfer = pinDimensions.x/3,
            edges = [FRONT+RIGHT, FRONT+LEFT, BACK+BOT],
            anchor = anchor, spin = spin, orient = orient) {
                // Pin overlap
                color_this($metalColor)
                position(BACK+TOP)
                cuboid(pinOverlapDimensions, rounding = pinOverlapDimensions.x/2,
                    edges = [BACK+RIGHT, BACK+LEFT],
                    anchor = FRONT+TOP);

            // Making attachable
            children();
        };
    }
}

/*
    Builds the body / base of the potentiometer

    oversizeBy : the amount the part should be oversized by
*/
module _BuildBody(oversizeBy, anchor = CENTER, spin = 0, orient = UP) {
    // Key values
    potentiometerDiameter = bodyDiameter + 2*oversizeBy;
    potentiometerHeight = bodyHeight + oversizeBy;

    anchors = [
        named_anchor("randomAnchor", [0, 5, 10], UP, 0)
    ];
    
    // Making attachable
    attachable(anchor, spin, orient, d = potentiometerDiameter, h = potentiometerHeight,
        anchors = anchors) {
        recolor($metalColor)
        intersection() {
            // Potentiometer
            zcyl(d = potentiometerDiameter, h = potentiometerHeight,
                rounding1 = bodyRounding) {
                    position(TOP+LEFT)
                    cuboid(tabDimensions + oversizeBy*[2,2,1],
                        rounding = min(tabDimensions)/2, except = [TOP, BOT],
                        anchor = BOT+LEFT);

            };

            // Outline
            zcyl(d = bodyDiameter + oversizeBy, h = 2*(bodyHeight + oversizeBy));
        }

        children();
    }
}


// ---------- Rendering Aids ----------

