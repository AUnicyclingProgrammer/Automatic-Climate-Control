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
bodyDiameter = 17;

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

// Diameter of the knob
knobDiameter = 6;

// Height of the knob
knobHeight = 8.5;

// Diameter of the tapered part of the knob (also the inner diameter of the splined part)
knobTaperDiameter = 4.75;

// Height of the tapered part of the knob
knobTaperHeight = 1;

// Height of the base of the knob
knobBaseHeight = 1.5;

// Number of splines on the knob (at least the number it would have if it didn't have the slot)
knobSplineCount = 18;

// Thickness of the slot in the knob
knobSlotThickness = 1;

/*[Misc.]*/
$metalColor = "lightGrey";
$pcbColor = "peru";

// oversize = false;

// ----- Global Variables -----
knobChamfer = (knobDiameter - knobTaperDiameter)/2;

// ----- Development -----

// ----- Constructing Assembly -----

*right(bodyDiameter + 5)
// expose_anchors()
BuildPotentiometer() {
    // show_anchors(s = 2);
};

*left(bodyDiameter + 5)
BuildPotentiometerHoleNegative() {
    // show_anchors(s = 2)
}

BuildPotentiometerDimensionsTest();


// ----- Modules and Functions -----
/*
    Generates a test print that can be used to confirm that the model has the same
        dimensions as the actual part in the real world.
*/
module BuildPotentiometerDimensionsTest() {
    testShapeBorder = 3;

    testShapeDimensions = [
        bodyDiameter,
        pcbDimensions.y + pinLength,
        bodyHeight + shaftHeight/2
    ] + [2*3,2*3,0];

    diff("potDiff")
    union() {
        // Test Shape Body
        cuboid(testShapeDimensions, chamfer = testShapeBorder/2) {
            // Cutting hole
            tag("potDiff")
            position(TOP+BACK)
            fwd(bodyDiameter/2 + testShapeBorder)
            BuildPotentiometerHoleNegative(anchor = "shaftCenter");
        };
    }
}

/*
    Builds a shape that can be subtracted to create a hole to mount the servo to.

    Has all potentiometer anchors
*/
module BuildPotentiometerHoleNegative(anchor = CENTER, spin = 0, orient = UP) {
    BuildPotentiometer(oversizeForNegative = get_slop(),
        anchor = anchor, spin = spin, orient = orient) children();
}

/*
    Build Potentiometer

    oversizeForNegative : if true, increases some dimensions by $slop so it can be used
        for making a negative
*/
module BuildPotentiometer(oversizeForNegative = 0,
    anchor = CENTER, spin = 0, orient = UP,
    $metalColor = "lightGrey", $pcbColor = "peru") {

    // Key Values
    oversizeBy = oversizeForNegative ? get_slop() : 0;
    
    potentiometerDiameter = bodyDiameter + 2*oversizeBy;
    potentiometerHeight = bodyHeight + oversizeBy;

    knobSplineHeight = knobHeight - knobBaseHeight - knobTaperHeight;

    toTopOfShaft = potentiometerHeight/2 + shaftHeight;
    toTopOfKnob = toTopOfShaft + knobHeight;

    // Making Attachable
    anchors = [
        // Shaft
        named_anchor("shaftBottom", [0,0,potentiometerHeight/2], DOWN, 0),
        named_anchor("shaftCenter", [0,0,potentiometerHeight/2 + shaftHeight/2], UP, 0),
        named_anchor("shaftTop", [0,0,toTopOfShaft], UP, 0),

        // Knob
        named_anchor("knobBottom", [0,0,toTopOfShaft], DOWN, 0),
        named_anchor("knobCenter", [0,0,toTopOfShaft + knobHeight/2], UP, 0),
        named_anchor("knobTop", [0,0,toTopOfKnob], UP, 0),

        // Splines
        named_anchor("splinesBottom", [0,0,toTopOfKnob - knobSplineHeight], DOWN, 0),
        named_anchor("splinesTop", [0,0,toTopOfKnob - knobSplineHeight/2], UP, 0),
        named_anchor("splinesTop", [0,0,toTopOfKnob], UP, 0),
    ];
    
    attachable(anchor, spin, orient,
        d = potentiometerDiameter, h = potentiometerHeight,
        anchors = anchors) {
        _BuildBody(oversizeBy) {
            // show_anchors(s = 3);

            // PCB and pins
            position(BOT)
            up(pcbPlacementHeight)
            _BuildPCBandPins(oversizeBy, anchor = BOT);

            // Shaft
            position(TOP)
            _BuildShaft(oversizeBy, anchor = BOT) {
                // Knob
                position(TOP)
                _BuildKnob();
            };
        };

        // For attachments
        children();
    }
}

/*
    Builds the knob
*/
module _BuildKnob(anchor = CENTER, spin = 0, orient = UP) {
    // Key values
    knobSplineHeight = knobHeight - knobBaseHeight - knobTaperHeight;

    // Making attachable
    attachable(anchor, spin, orient, d = knobDiameter, h = knobHeight) {
        color_this($metalColor)
        // render()
        tag_scope()
        diff("knobDiff") {
            // Base
            zcyl(d = knobDiameter, h = knobBaseHeight, chamfer2 = knobChamfer,
                anchor = BOT);

            // Taper
            up(knobBaseHeight)
            zcyl(d = knobTaperDiameter, h = knobTaperHeight,
                anchor = BOT);
    
            // Splines
            up(knobBaseHeight + knobTaperHeight)
            zcyl(d = knobDiameter, h = knobSplineHeight, chamfer = knobChamfer,
                anchor = BOT);

            /* Not going to worry about adding the splines, it makes it lag and I
            don't actually need the extra detail */

            /* Best spline code I came up with, laggy but renders correctly
            sliceAngle = 4*360/knobSplineCount;

            tag("knobDiff")
            zrot_copies(n = knobSplineCount)
            right(knobDiameter/2 - knobChamfer)
            zrot(-sliceAngle/2)
            up(knobBaseHeight + knobTaperHeight)
            pie_slice(ang = sliceAngle, r = 1.5*knobChamfer, l = knobHeight + 2*scooch,
                $fn = 8); */

            // Slot
            slotDimensions = [knobDiameter + 2*scooch, knobSlotThickness, knobHeight];

            tag("knobDiff")
            up(knobBaseHeight)
            cuboid(slotDimensions, anchor = BOT);
        }

        children();
    }
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
            anchor = anchor, spin = spin, orient = orient) children();
    } else {
        down(scooch)
        zcyl(h = shaftHeight + 2*scooch, d = shaftDiameter + 2*oversizeBy,
            anchor = anchor, spin = spin, orient = orient) children();
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

    pcbCuboidDimensions = pcbDimensions + oversizeBy*[2,2,2 + 2]
        -[0,potentiometerDiameter/2,0];

    // Building PCB
    union() {
        // Part that goes through potentiometer body
        color_this($pcbColor)
        up(2*oversizeBy)
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
                    up(scooch)
                    back(pinOverlapDimensions.y + bodyDiameter/2)
                    cuboid([pcbCuboidDimensions.x,
                        pinDimensions.y + pinOverlapDimensions.y + bodyDiameter/2,
                        bodyHeight - pcbPlacementHeight + 3*oversizeBy]
                        + get_slop()*[0,2,2],
                        rounding = pcbCuboidDimensions.z/2, edges = [FRONT+RIGHT, FRONT+LEFT],
                        anchor = BACK+TOP
                    );

                    // "Extending" PCB
                    position(FRONT)
                    cuboid([pcbCuboidDimensions.x,
                        pinDimensions.y + 2*get_slop(),
                        pcbCuboidDimensions.z],
                        rounding = pcbCuboidDimensions.z/2, edges = [FRONT+RIGHT, FRONT+LEFT],
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
    
    // Making attachable
    attachable(anchor, spin, orient, d = potentiometerDiameter, h = potentiometerHeight) {
        recolor($metalColor)
        intersection() {
            // Potentiometer
            zcyl(d = potentiometerDiameter, h = potentiometerHeight,
                rounding1 = bodyRounding) {
                    position(TOP+LEFT)
                    down(scooch)
                    cuboid(tabDimensions + oversizeBy*[2,2,1],
                        rounding = min(tabDimensions)/2, except = [TOP, BOT],
                        anchor = BOT+LEFT);

            };

            // Outline
            zcyl(d = potentiometerDiameter, h = 2*(bodyHeight + oversizeBy));
        }

        children();
    }
}


// ---------- Rendering Aids ----------

