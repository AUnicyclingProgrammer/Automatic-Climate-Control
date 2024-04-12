// Includes
include <BOSL2/std.scad>
include <BOSL2/threading.scad>
include <BOSL2/structs.scad>
include <BOSL2/hinges.scad>
include <BOSL2/screws.scad>
include <BOSL2/beziers.scad>

include <OU-OSL.scad>

// $fn to use for previewing
$preview_fn = 32;

// $fn to use when rendering
$render_fn = 90;

$fn = $preview ? $preview_fn : $render_fn; // Number of fragments used to draw a circle, first number is used for previewing, second is used for rendering

/* 
    // Minimum angle to use when previewing
    $preview_fa = 4.0; //0.1

    // Minimum angle to use when rendering
    $render_fa = 2.0; //0.1

    $fa = $preview ? $preview_fa : $render_fa;

    // Minimum size (in mm) to use when previewing
    $preview_fs = 0.25; //0.01

    // Minimum size (in mm) to use when rending
    $render_fs = 0.10; //0.01

    $fs = $preview ? $preview_fs : $render_fs;
*/

/*
Slop per layer height
0.2 standard quality printing: 0.2
0.32 fastRender prototyping: 0.4

$parent_size.x saving for later, super helpful
*/

$slop = 0.2; // mm, closest faces can be and still move a bit
scooch = 0.010; //0.001 //Just for making sure parts actually go together

/*
    Model of the generic micro size servo from SparkFun
    Link: https://www.sparkfun.com/products/10189
    Manufacturer Link: http://www.springrc.com/en/pd.jsp?id=88#_jcp=3_50

    Because this is a stand-alone file, all values are global values
*/

/*[Preview]*/


// ----- Parameters -----

/*[Servo Dimensions]*/
// Length of the servo body
servoBodyLength = 16.75;

// Width of the servo body
servoBodyWidth = 32;

// Height of the servo body
servoBodyHeight = 28;

servoBodyDimensions = [servoBodyLength, servoBodyWidth, servoBodyHeight];

// Height of the chamfer on the front of the servo
frontChamferHeight = 3.5;

// Length of the chamfer on the front of the servo
frontChamferLength = 6.5;

/*[Mounting]*/

// Vertical distance between the bottom of the servo body and the bottom of the mounting plate
mountingPlatePlacementHeight = 18.5;

// Thickness of the mounting plate
mountingPlateThickness = 2.5;

// Length of the mounting plate
mountingPlateLength = servoBodyDimensions.x; // Specs say it should be 16.5

// Width of the mounting plate
mountingPlateWidth = 42.8;

mountingPlateDimensions = [mountingPlateLength, mountingPlateWidth, mountingPlateThickness];

// Distance between the screw holes for mounting the servo (shorter distance)
mountingHoleSpacingWidth = 8;

// Distance between the screw holes for mounting (longer distance)
mountingHoleSpacingLength = 38;

// Diameter of the mounting screw holes
mountingHoleDiameter = 4;

// Width of the slot for each hole at the edge of the bracket
mountingHoleSlotWidth = 2.2;

/* [Servo Interface] */

// Distance the interface is from the back of the servo
interfaceDistanceFromBack = 8;

// Outline of the ring around the interface on the top of the servo
interfaceOutlineDiameter = 10;

// Height of the ring around the interface on the top of the servo
interfaceOutlineHeight = 1.6;

// Number of splines on the servo interface
interfaceSplineCount = 24;

// Height of the interface
interfaceHeight = 3;

// Outer diameter of the servo interface
interfaceOuterDiameter = 4.9;

// Inner diameter of the servo interface
interfaceInnerDiameter = 3.7;

/* [Wires] */

// Length of the base of the prismoid that the wires come out of
wireOutletBaseLength = 6.5;

// Height of the base of the prismoid that the wires come out of
wireOutletBaseHeight = 4;

wireOutletBaseDimensions = [wireOutletBaseLength, wireOutletBaseHeight];

// Length of the top of the prismoid that the wires come out of
wireOutletTopLength = 4.5;

// Height of the top of the prismoid that the wires come out of
wireOutletTopHeight = 3;

wireOutletTopDimensions = [wireOutletTopLength, wireOutletTopHeight];

// Distance that the wire outlet protrudes from the servo
wireOutletThickness = 1.5;

// Vertical distance between the bottom of the servo body and the bottom of the wire outlet
wireOutletPlacementHeight = 4;

// Diameter of the servo wires
wireDiameter = 1.25;


/*[Misc.]*/
// Rounding to apply to the vertical edges, value is approximate
verticalEdgeRounding = 1.5;

// ----- Development -----


// ----- Constructing Assembly -----
// expose_anchors()
BuildMicroServo() {
    // show_anchors(s = 3);
};


// ----- Modules and Functions -----
/*
    Builds an attachable micro size servo

    Modeled after the SpringRC SM-S3317SR
*/
module BuildMicroServo(anchor = CENTER, spin = 0, orient = UP) {
    toMountCenter = [0,0,-servoBodyDimensions.z/2 + mountingPlatePlacementHeight + mountingPlateDimensions.z/2];
    mountReferenceLocation = [mountingHoleSpacingWidth/2, mountingHoleSpacingLength/2, mountingPlateDimensions.z/2];

    anchors = [
        // Interface
        named_anchor("interfaceTop", [0, servoBodyDimensions.y/2 - interfaceDistanceFromBack, servoBodyDimensions.z/2 + interfaceOutlineHeight + interfaceHeight], UP, 0),
        named_anchor("interfaceCenter", [0, servoBodyDimensions.y/2 - interfaceDistanceFromBack, servoBodyDimensions.z/2 + interfaceOutlineHeight + interfaceHeight/2], UP, 0),
        named_anchor("interfaceBottom", [0, servoBodyDimensions.y/2 - interfaceDistanceFromBack, servoBodyDimensions.z/2 + interfaceOutlineHeight], UP, 0),

        // Top of Bracket
        named_anchor("topBackRightMount", toMountCenter + ApplyVectorMultiplicationMask(mountReferenceLocation, [1,1,1]), UP, 0),
        named_anchor("topBackLeftMount", toMountCenter + ApplyVectorMultiplicationMask(mountReferenceLocation, [-1,1,1]), UP, 0),
        named_anchor("topFrontRightMount", toMountCenter + ApplyVectorMultiplicationMask(mountReferenceLocation, [1,-1,1]), UP, 0),
        named_anchor("topFrontLeftMount", toMountCenter + ApplyVectorMultiplicationMask(mountReferenceLocation, [-1,-1,1]), UP, 0),
        
        // Bottom of Bracket
        named_anchor("bottomBackRightMount", toMountCenter + ApplyVectorMultiplicationMask(mountReferenceLocation, [1,1,-1]), DOWN, 0),
        named_anchor("bottomBackLeftMount", toMountCenter + ApplyVectorMultiplicationMask(mountReferenceLocation, [-1,1,-1]), DOWN, 0),
        named_anchor("bottomFrontRightMount", toMountCenter + ApplyVectorMultiplicationMask(mountReferenceLocation, [1,-1,-1]), DOWN, 0),
        named_anchor("bottomFrontLeftMount", toMountCenter + ApplyVectorMultiplicationMask(mountReferenceLocation, [-1,-1,-1]), DOWN, 0),

        // Bracket Middle Slice
        named_anchor("bracketBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,0,-1]), DOWN, 0),
        named_anchor("bracketCenter", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,0,0]), UP, 0),
        named_anchor("bracketTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,0,1]), UP, 0),
        
        named_anchor("bracketRightBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,0,-1]), RIGHT+DOWN, 0),
        named_anchor("bracketRight", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,0,0]), RIGHT, 0),
        named_anchor("bracketRightTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,0,1]), RIGHT+UP, 0),
        
        named_anchor("bracketLeftBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,0,-1]), LEFT+DOWN, 0),
        named_anchor("bracketLeft", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,0,0]), LEFT, 0),
        named_anchor("bracketLeftTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,0,1]), LEFT+UP, 0),
        
        // Bracket Back Slice
        named_anchor("bracketBackBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,1,-1]), BACK+DOWN, 0),
        named_anchor("bracketBackCenter", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,1,0]), BACK, 0),
        named_anchor("bracketBackTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,1,1]), BACK+UP, 0),
        
        named_anchor("bracketBackRightBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,1,-1]), BACK+RIGHT+DOWN, 0),
        named_anchor("bracketBackRight", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,1,0]), BACK+RIGHT, 0),
        named_anchor("bracketBackRightTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,1,1]), BACK+RIGHT+UP, 0),
        
        named_anchor("bracketBackLeftBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,1,-1]), BACK+LEFT+DOWN, 0),
        named_anchor("bracketBackLeft", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,1,0]), BACK+LEFT, 0),
        named_anchor("bracketBackLeftTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,1,1]), BACK+LEFT+UP, 0),

        // Bracket Front Slice
        named_anchor("bracketFrontBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,-1,-1]), FRONT+DOWN, 0),
        named_anchor("bracketFrontCenter", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,-1,0]), FRONT, 0),
        named_anchor("bracketFrontTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[0,-1,1]), FRONT+UP, 0),
        
        named_anchor("bracketFrontRightBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,-1,-1]), FRONT+RIGHT+DOWN, 0),
        named_anchor("bracketFrontRight", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,-1,0]), FRONT+RIGHT, 0),
        named_anchor("bracketFrontRightTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[1,-1,1]), FRONT+RIGHT+UP, 0),
        
        named_anchor("bracketFrontLeftBottom", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,-1,-1]), FRONT+LEFT+DOWN, 0),
        named_anchor("bracketFrontLeft", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,-1,0]), FRONT+LEFT, 0),
        named_anchor("bracketFrontLeftTop", toMountCenter + ApplyVectorMultiplicationMask(mountingPlateDimensions/2,[-1,-1,1]), FRONT+LEFT+UP, 0),
    ];
    attachable(anchor, spin, orient, size = servoBodyDimensions,
        anchors = anchors) {
        recolor("dimGrey")
        _BuildBody() {
            position(TOP+BACK)
            fwd(interfaceDistanceFromBack)
            _BuildServoInterface(anchor = BOT);

            position(BOT)
            up(mountingPlatePlacementHeight)
            _BuildMountingPlate();

            position(BACK)
            down(servoBodyDimensions.z/2 - wireOutletBaseDimensions.y/2)
            up(wireOutletPlacementHeight)
            _BuildWireOutlet(anchor = BOT, orient = BACK, spin = 0) {
                
            };
        };

        children();
    }
}

/*
    Builds the trapezoidal shape that protects the wires where they come
        out of the servo.
*/
module _BuildWireOutlet(anchor = CENTER, spin = 0, orient = UP) {
    prismoid(size1=wireOutletBaseDimensions, size2=wireOutletTopDimensions,
        h=wireOutletThickness,
        anchor = anchor, spin = spin, orient = orient) {
            position(TOP)
            xcopies(n = 3, spacing = wireDiameter)
                let(color = $idx % 3 == 0
                    ? "whiteSmoke"
                    : $idx % 3 == 1
                        ? "red"
                        : "darkSlateGrey")
                color_this(color)
                sphere(d = wireDiameter);
        
            children();
    };
}

/*
    Builds the servo interface
*/
module _BuildServoInterface(anchor = CENTER, spin = 0, orient = UP) {
    // Interface Outline
    zcyl(d = interfaceOutlineDiameter, h = interfaceOutlineHeight,
        chamfer2 = interfaceOutlineHeight/2,
        anchor = anchor, spin = spin, orient = orient) {
        
        // Interface with Splines
        interfaceRegion = star(n = 24,
            od = interfaceOuterDiameter, id = interfaceInnerDiameter);
        
        color_this("gainsboro")
        attach(TOP, BOT)
        linear_sweep(interfaceRegion, h = interfaceHeight);
        
        // Attachment support
        children();
    };
}

/*
    Builds the body of the servo
*/
module _BuildBody(anchor = CENTER, spin = 0, orient = UP) {
    tag_scope()
    diff()
    cuboid(servoBodyDimensions, rounding = verticalEdgeRounding, except = [TOP, BOT],
        anchor = anchor, spin = spin, orient = orient) {
        move([0,-scooch,scooch])
        tag("remove")
        position(TOP+FRONT)
        wedge([servoBodyDimensions.x + 2*scooch, frontChamferLength, frontChamferHeight], 
            anchor = BOT+FRONT, orient = DOWN);

        children();
    };
};

/*
    Buildings the mounting plate for the servo
*/
module _BuildMountingPlate() {
    // --- Calculations and Definitions ---
    holeHeight = mountingPlateDimensions.z + 2*scooch;
    
    // --- Building Mounting Plate ---
    up(mountingPlateDimensions.z/2)
    difference() {
        // Mounting Plate
        cuboid(mountingPlateDimensions, rounding = verticalEdgeRounding,
            except = [TOP, BOT]);

        // Screw Holes
        grid_copies(n = 2, spacing = [mountingHoleSpacingWidth, mountingHoleSpacingLength]) {
            // Hole
            zcyl(d = mountingHoleDiameter, h = holeHeight);
            
            // Slot
            slotDimensions = [mountingHoleDiameter, mountingHoleSlotWidth, holeHeight];
            
            zrot(sign($pos.y)*90)
                cuboid(slotDimensions, anchor = LEFT);
        }
    }
}




// ---------- Rendering Aids ----------

