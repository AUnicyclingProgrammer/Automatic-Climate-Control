// Includes
include <BOSL2/std.scad>
include <BOSL2/threading.scad>
include <BOSL2/structs.scad>
include <BOSL2/hinges.scad>
include <BOSL2/screws.scad>
include <BOSL2/beziers.scad>
include <BOSL2/gears.scad>

include <OU-OSL.scad>

// Use means reference these files, include means run these files
use <MicroServo.scad>
use <PotentiometerB500K.scad>

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
    Building a geometry that will allow me to connect the output of the potentiometer
    to the output of the servo so the servo will be able to turn the potentiometer
    without directly coupling them together (in case the code malfunctions)
*/

/*[Preview]*/

// If true renders the assembly, otherwise printing mode is used
renderAssembly = true;

printServoGear = false;
printPotentiometerGear = false;
printMountingPlate = true;

/*[Mechanism]*/

// Distance between the centers of the gears (which defines where the servo and potentiometer need placed)
// There is no good way to do this easily

// Thickness of the gears
gearThickness = 6;

// Number of teeth the gears will have
gearToothCount = 14;

// Distance between the centers of the gear teeth, measured in mm
gearCircularPitch = 6;

// Helical angle of the gears
gearHelicalAngle = 37;

/* [Mounting Plate] */

// Dimensions to make the mounting plate
mountingPlateDimensions = [70, 47, 8];

// For aligning the plate
mountingPlateTranslation = [0, -8];

// Clearance between the gears and the mounting plate
mountingPlateGearClearance = 5;

/* [Potentiometer Interface] */

// Diameter to make the hole in the gear that goes on the potentiometer
potentiometerInterfaceDiameter = 6;

// ----- Parameters -----

/*[Misc.]*/

// ----- Global Variables -----
/*
Variables that can be referenced by anything but that don't matter much. Things like
cosmetic chamfers or fillets would fall into this category
*/

mountingPlateChamfer = 2;


// ----- Development -----
// gear_dist() Example1
*up(0) {
    circ_pitch=5; teeth1=7; teeth2=24;
    d = gear_dist(circ_pitch=circ_pitch, teeth1, teeth2);
    spur_gear2d(circ_pitch, teeth1, gear_spin=-90);
    right(d) spur_gear2d(circ_pitch, teeth2, gear_spin=90-180/teeth2);
}

// gear_dist() Example2
*up(0) {
    circ_pitch=5; teeth1=7; teeth2=24; helical=37;
    d = gear_dist(circ_pitch=circ_pitch, teeth1, teeth2, helical);
    spur_gear(circ_pitch, teeth1, helical=helical, gear_spin=-90,slices=15);
    right(d) spur_gear(circ_pitch, teeth2, helical=-helical, gear_spin=-90-180/teeth2,slices=9);
}

// Using gear_dist to make two gears that mesh
*up(0) {
    d = gear_dist(circ_pitch=gearCircularPitch, gearToothCount, gearToothCount,
        gearHelicalAngle, backlash=get_slop());
    spur_gear(gearCircularPitch, gearToothCount, thickness = gearThickness,
        helical=gearHelicalAngle, gear_spin=-90, slices=round($fn/4),
        herringbone = true);
    right(d) spur_gear(gearCircularPitch, gearToothCount, thickness = gearThickness,
        helical=-gearHelicalAngle, gear_spin=-90-180/gearToothCount, slices=round($fn/4),
        herringbone = true);
}

// ----- Constructing Assembly -----

displacementDistance = CalculateGearDistance(backlash = get_slop());


if (renderAssembly) {
    // Mounting Plate
    down(gearThickness/2)
    down(mountingPlateGearClearance)
    BuildTestingMount(displacement = displacementDistance);
    
    // Gear for the potentiometer
    right(displacementDistance/2) {
        BuildPotentiometerGear() {
            tag("keep")
            position(TOP)
            BuildPotentiometer(anchor = "knobTop");
        };
    }

    // Gear for the servo
    left(displacementDistance/2) {
        BuildServoGear() {
            // Visual Reference
            tag("keep")
            position(BOTTOM)
            BuildMicroServoHorn(anchor = "bottomFace") {
                position("interface")
                BuildMicroServo(anchor="interfaceTop");
            };
        };
    }
} else {
    if (printServoGear) {
        BuildServoGear();
    }

    if (printPotentiometerGear) {
        BuildPotentiometerGear();
    }

    if (printMountingPlate) {
        BuildTestingMount(displacement = displacementDistance);
    }
}


// ----- Modules and Functions -----

/*
    Builds the mounting plate for testing

    dimensions : size to make the mounting plate
    displacement : distance there should be between the servo and the potentiometer
*/
module BuildTestingMount(displacement) {
    move(mountingPlateTranslation)
    diff("testingMountDiff")
    cuboid(mountingPlateDimensions, chamfer = mountingPlateChamfer,
        anchor = TOP)
        // Making origin flush with bottom center of gears
        position(TOP) up(mountingPlateGearClearance) fwd(mountingPlateTranslation.y) {
            // Potentiometer
            tag("testingMountDiff")
            right(displacement/2)
            up(gearThickness)
            BuildPotentiometerHoleNegative(anchor = "knobTop");
            
            // Servo
            force_tag("testingMountDiff")
            left(displacement/2)
            BuildMicroServoHorn(anchor = "bottomFace") {
                position("interface")
                BuildMicroServoHoleNegative(disableWireTrack = true, topMount = true,
                    anchor = "interfaceTop");
            };
        };
}

/*
    Builds the gear that goes on the potentiometer

    This gear is the one that has the positive helical angle
*/
module BuildPotentiometerGear(anchor = CENTER, spin = 0, orient = UP) {
    tag_scope()
    diff("potGearDiff")
    spur_gear(gearCircularPitch, gearToothCount, thickness = gearThickness,
        helical=gearHelicalAngle, gear_spin=-90, slices=round($fn/4),
        herringbone = true,
        anchor=anchor, spin=spin, orient=orient) {
        
        // So it's attachable
        tag("keep")
        children();

        // Cutting out middle for potentiometer
        tag("potGearDiff")
        zcyl(d = potentiometerInterfaceDiameter, h = gearThickness + 2*scooch);
    };
}

/*
    Builds the gear that will go on the servo

    This gear is the one that has the negative helical angle (and the
    teeth are rotated for better alignment)
*/
module BuildServoGear(anchor = CENTER, spin = 0, orient = UP) {
    tag_scope()
    diff("servoGearDiff")
    spur_gear(gearCircularPitch, gearToothCount, thickness = gearThickness,
        helical=-gearHelicalAngle, gear_spin=-90-180/gearToothCount, slices=round($fn/4),
        herringbone = true,
        anchor=anchor, spin=spin, orient=orient) {
        
        // So it's attachable
        tag("keep")
        children();

        // Making slot for servo horn
        position(BOT)
        down(scooch)
        tag("servoGearDiff")
        BuildMicroServoHornNegative(anchor = "bottomFace");
    };
}

/*
    Returns the distance between the two gears

    Just a wrapper around gear_dist for this particular use case

    backlash : how much backlash to put between the gears
*/
function CalculateGearDistance(backlash = 0) = 
    gear_dist(circ_pitch=gearCircularPitch, gearToothCount, gearToothCount,
        helical=gearHelicalAngle, backlash=backlash);
// 


// ---------- Rendering Aids ----------

