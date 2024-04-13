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
    Description
*/

/*[Preview]*/

// ----- Parameters -----

/*[Misc.]*/

// ----- Development -----


// ----- Constructing Assembly -----

// ----- Modules and Functions -----


// ---------- Rendering Aids ----------

