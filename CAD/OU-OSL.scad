include <BOSL2/std.scad>
include <BOSL2/threading.scad>

/*
Name Idea Taken from BOSL2
OrangeUnicycle's OpenSCAD Library - OU-OSL

========== Best Practices ==========

Naming Conventions:
* Calculate - For functions that return values
* Create - For functions that create data structures
* Generate - For functions that return regions or paths
* Build - For modules that create 3D geometries
* Draw - For modules that create 2D geometries
*/


// ========== Utility Functions ==========
// ===== Mirroring =====
module MirrorYZ(duplicateObject = true) {
    if (duplicateObject) {
        children();
    }
    xflip() children();
}

module MirrorXZ(duplicateObject = true) {
    if (duplicateObject) {
        children();
    }
    yflip() children();
}

module MirrorXY(duplicateObject = true) {
    if (duplicateObject) {
        children();
    }
    zflip() children();
}

// ===== Basic Math =====
/*
    Performs the XOR operation
*/
function XOR(a, b) = (!a && b) || (a && !b);

// ===== Lists and Matrices =====

/*
    Applies the multiplication mask to the provided vector (or list) and returns the result.
    This function essentially performs element-wise multiplication

    vector : vector / list to apply the multiplication mask to
    mask : multiplication mask to apply
*/
function ApplyVectorMultiplicationMask(vector, mask) =
    assert(is_def(vector), "vector must be provided")
    assert(is_def(mask), "mask must be provided")
    assert(len(vector) == len(mask), "vector and mask must be the same length")
    let(
    result = [
        for (i = [0:len(vector) - 1])
            vector[i]*mask[i]
    ]
    ) result;
//

/*
    Extracts the data from a specific row in a 2D table and returns it as a list

    grid : 2d array
    rowIndex : index of row
*/
function ExtractRow(grid, rowIndex) =
    let(
        gridDimensions = list_shape(grid),
        extractedRow = [
            for(j = [0:gridDimensions[1]-1])
                grid[rowIndex][j]
        ]
    ) extractedRow;
//

/*
    Extracts the data from a specific column in a 2D table and returns it as a list

    grid : 2d array
    Index : index of column
*/
function ExtractColumn(grid, columnIndex) =
    let(
        gridDimensions = list_shape(grid),
        extractedColumn = [
            for(i = [0:gridDimensions[0]-1])
                grid[i][columnIndex]
        ]
    ) extractedColumn;
//

/*
    Performs a boolean index selection on each element / item in a list

    list : list to iterate over
    indicies : indicies of each list item to keep
*/
function ExtractElementIndicies(list, indicies) =
    [for (pt = list) bselect(pt, indicies)];
//

/*
    Performs the not operation on every element in a boolean list

    list : boolean list to invert
*/
function NotBooleanList(list) = [for (i = list) !i];
//

// ===== Paths and Regions =====

/*
    Generates the bounding box for a given path
    (This is my complicated version, I made an issue on BOSL2 for this and they
    proposed a much simpler version. It wasn't as useful as I thought though)
*/
function GeneratePathBoundingBox(path) =
    let(
        bounds = pointlist_bounds(path),
        
        xLen = abs(bounds[0].x - bounds[1].x),
        yLen = abs(bounds[0].y - bounds[1].y),

        center = mean(bounds),

        bounding_box = move(center, p = rect([xLen, yLen]))
    ) bounding_box;
//

/*
    Clamps all values in the path or region to +X, cutting off anything past 0

    This is useful for cleaning data before performing rotate_sweep() or other similar
    operations.
*/ 
function ClampToPositiveX(pathOrRegion) =
    let(
        isPath = is_path(pathOrRegion),
        isRegion = is_region(pathOrRegion))
    assert(isPath || isRegion, str("Input must either be a path or region"))
    let(
        unprocessedPath = isPath ? pathOrRegion : force_path(pathOrRegion),

        clampedPath = [for (point = unprocessedPath)
            if(point.x < 0) [0, point.y]
            else [point.x, point.y]],

        output = isRegion ? make_region(clampedPath) : clampedPath
    ) output;
//

/*
    Clamps all values in the path or region to specified bounds, cutting off anything
    outside the boundaries (removes duplicate and collinear points by default)

    This is useful for cleaning data before performing rotate_sweep() or other similar
    operations.

    pathOrRegion : path or region to clamp
    bounds : [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    clean : if true, cleans the output (removes duplicate and collinear points)
*/ 
function ClampTo(pathOrRegion, bounds, clean = true) =
    assert(is_def(pathOrRegion), "A path or region must be specified")
    assert(is_def(bounds), "bounds must be provided")
    let(
        isPath = is_path(pathOrRegion),
        isRegion = is_region(pathOrRegion),
        is2dPath = len(bounds[0]) == 2 || isRegion)
    assert(isPath || isRegion, str("Input must either be a path or region"))
    assert(is_path(bounds), "Invalid bounds format")
    assert(len(bounds) == 2, "bounds must only contain two items, the minimum bounding point and the maximum mounting point")
    assert(len(bounds[0]) == 2 || len(bounds[0]) == 3, "the first item in bounds must be either a 2d or 3d point")
    assert(len(bounds[1]) == 2 || len(bounds[1]) == 3, "the second item in bounds must be either a 2d or 3d point")
    let(
        minBounds = is2dPath ? [bounds[0].x, bounds[0].y, 0] : bounds[0],
        maxBounds = is2dPath ? [bounds[1].x, bounds[1].y, 0] : bounds[1])
    assert(minBounds.x <= maxBounds.x, "min x must be less than or equal to max x")
    assert(minBounds.y <= maxBounds.y, "min y must be less than or equal to max y")
    assert(minBounds.z <= maxBounds.z, "min z must be less than or equal to max z")
    let(
        unprocessedPath = isPath ? pathOrRegion : force_path(pathOrRegion),

        xClampedPath = [for (point = path3d(unprocessedPath))
            if(point.x < minBounds.x) [minBounds.x, point.y, point.z]
            else if (point.x > maxBounds.x) [maxBounds.x, point.y, point.z]
            else [point.x, point.y, point.z]],
        
        xyClampedPath = [for (point = xClampedPath)
            if(point.y < minBounds.y) [point.x, minBounds.y, point.z]
            else if (point.y > maxBounds.y) [point.x, maxBounds.y, point.z]
            else [point.x, point.y, point.z]],
        
        xyzClampedPath = [for (point = xyClampedPath)
            if(point.z < minBounds.z) [point.x, point.y, minBounds.z]
            else if (point.z > maxBounds.z) [point.x, point.y, maxBounds.z]
            else [point.x, point.y, point.z]],
        
        clampedPath = is2dPath ? path2d(xyzClampedPath) : xyzClampedPath,

        clampedOutput = isRegion ? make_region(clampedPath) : clampedPath,

        output = clean ? CleanPathOrRegion(clampedOutput) : clampedOutput
    ) output;
//

/*
    Removes extra collinear points from a simple region.

    region : region to clean
    test_valid : if true, performs m
*/
function SimpleRegionMergeCollinear(region) =
    make_region(
        path_merge_collinear(
            path = force_path(region),
        closed = true));
//

/*
    Removes duplicate, consecutive points in a simple region. Useful for when parallelization
    errors occur.
    
    Deduplicate doesn't actually work on regions, it can delete the entire region and return
        an empty string

    region : region to deduplicate
*/
function DeduplicateRegion(region) =
    let(
        path = force_path(region),
        deduplicatedPath = deduplicate(path, closed = true),
        deduplicatedRegion = make_region(deduplicatedPath)
    ) deduplicatedRegion;
//

/*
    "Cleans" a path or simple region by removing all duplicate and collinear points
*/
function CleanPathOrRegion(pathOrRegion) = 
    assert(is_def(pathOrRegion), "A path or region must be specified")
    let(
        isPath = is_path(pathOrRegion),
        isRegion = is_region(pathOrRegion)
    )
    assert(isPath || isRegion, str("Input must either be a path or region"))
    let(        
        output = isPath
            // It is a path
            ? path_merge_collinear(deduplicate(pathOrRegion))
            // It is a region
            : SimpleRegionMergeCollinear(DeduplicateRegion(pathOrRegion))
    ) output;
//

// ===== Structures =====
/*
    Creates a structure from a list of key and value pairs (where a pair is a list
        containing 1 key and 1 value)
*/
function CreateStructFromKeyValuePairs(keyValueList) =
    let(
        keyValueParis = flatten(keyValueList),
        
        // Creating Structure (Modification allowed so echo_struct() can be used)
        struct = struct_set([], keyValueParis)
    ) struct;
//

// ========== Visualization Tools ==========
// ===== Troubleshooting =====
/*
    Cuts a sphere into 2 octants completely opposite from each other, allowing a visual
    indicator of where the center of the sphere is, and also any objects at or behind the
    center of the sphere.

    diameter : diameter of the indicator sphere
*/
module IndicatorSphere(diameter, anchor = CENTER, spin = 0, orient = UP) {
    attachable(anchor, spin, orient, d = diameter) {
        difference() {
            sphere(d=diameter);

            _cutoutCuboids(diameter);
            
            xrot(90)
            _cutoutCuboids(diameter);

            // For cleaning up the cut, doesn't technically remove material
            zrot(-90)
            _cutoutCuboids(diameter);
        }
        children();
    }
    
    module _cutoutCuboids(diameter) {
        cutoutCuboidDim = [diameter/2, diameter, diameter/2];
            
        move([-cutoutCuboidDim.x/2,0,cutoutCuboidDim.z/2])
        cuboid(cutoutCuboidDim);
        
        move([cutoutCuboidDim.x/2,0,-cutoutCuboidDim.z/2])
        cuboid(cutoutCuboidDim);
    }
}

// ===== Partitioning =====
/*
    Masks off the geometry of child objects in the region of the specified anchor

    Heavily based on the BOSL2 partition functions and some code recommended
    by one of the creators of BOSL2: https://github.com/BelfrySCAD/BOSL2/issues/1397#issuecomment-1974292060

    anchor : anchor indicating which part of the model should be removed
    s : size of the partitioning cuboid
    disabled : if true, will not remove material
*/
module MaskOff(anchor, s=100, disabled = false) {
    // Assertions
    assert(is_def(anchor), "anchor must be provided");
    req_children($children);

    // Removing material from desired location
    difference() {
        children();

        if (!disabled) {
            cuboid(s, anchor = anchor);
        }
    }
}

// ========== Geometry and Trig Functions ==========
// ===== Basic Trig and Geometry Functions =====
/*
    Calculates the vertical length that results after a line of a specified length
    is rotated.
    (Just a sine function behind the scenes)
*/
function CalculateVerticalLengthAfterRotation(objectLength, angle) = objectLength*sin(angle);
//

/*
    Calculates the horizontal length that results after a line of a specified length
    is rotated.
    (Just a cosine function behind the scenes)
*/
function CalculateHorizontalLengthAfterRotation(objectLength, angle) = objectLength*cos(angle);
//

/*
    Computes the distance (technically magnitude) between two points
*/
function CalculatePointDistance(pt1, pt2) =
    assert(is_def(pt1), "pt1 must be defined")
    assert(is_def(pt2), "pt2 must be defined")
    let(
        pt1Shape = list_shape(pt1),
        pt2Shape = list_shape(pt2)
    )
    assert(pt1Shape == pt2Shape, "pt1 and pt2 must both be 2D or 3D points")
    assert(pt1Shape == [2] || pt1Shape == [3], "pt1 must be either a 2D or 3D point")
    assert(pt2Shape == [2] || pt2Shape == [3], "pt1 must be either a 2D or 3D point")
    let(
        is2D = (pt1Shape == [2]),

        pt1Processed = is2D ? [pt1.x, pt1.y, 0] : pt1,
        pt2Processed = is2D ? [pt2.x, pt2.y, 0] : pt2,
        
        xDifference = (pt1Processed.x - pt2Processed.x)*(pt1Processed.x - pt2Processed.x),
        yDifference = (pt1Processed.y - pt2Processed.y)*(pt1Processed.y - pt2Processed.y),
        zDifference = (pt1Processed.z - pt2Processed.z)*(pt1Processed.z - pt2Processed.z),

        dist = sqrt(xDifference + yDifference + zDifference))
    dist;
//

// ===== Geometric Analysis =====

/*
    Determines the bounding points for a path or region along the x axis.
*/
function CalculatePathXBounds(pathOrRegion) =
    let(
        path = force_path(pathOrRegion),

        pathBounds = pointlist_bounds(path),

        bounds = [pathBounds[0].x, pathBounds[1].x]
    )
    bounds;
//

/*
    Calculates the magnitude of the line segment between the x bounds of the path
*/
function CalculatePathXLength(pathOrRegion) =
    let(
        bounds = CalculatePathXBounds(pathOrRegion),

        length = CalculatePointDistance([bounds[0],0], [bounds[1],0])
    ) length;
//

/*
    Determines the bounding points for a path or region along the y axis.
*/
function CalculatePathYBounds(pathOrRegion) =
    let(
        path = force_path(pathOrRegion),

        pathBounds = pointlist_bounds(path),

        bounds = [pathBounds[0].y, pathBounds[1].y]
    )
    bounds;
//

/*
    Calculates the magnitude of the line segment between the y bounds of the path
*/
function CalculatePathYLength(pathOrRegion) =
    let(
        bounds = CalculatePathYBounds(pathOrRegion),

        length = CalculatePointDistance([bounds[0],0], [bounds[1],0])
    ) length;
//

/*
    Determines the bounding points for a path or region along the z axis.
*/
function CalculatePathZBounds(pathOrRegion) =
    let(
        path = force_path(pathOrRegion),

        pathBounds = pointlist_bounds(path),

        bounds = [pathBounds[0].z, pathBounds[1].z]
    )
    bounds;
//

/*
    Calculates the magnitude of the line segment between the z bounds of the path
*/
function CalculatePathZLength(pathOrRegion) =
    let(
        bounds = CalculatePathZBounds(pathOrRegion),

        length = CalculatePointDistance([bounds[0],0], [bounds[1],0])
    ) length;
//

// ===== Circle and Arc Functions =====

/*
    Function that determines the radius of an arc given it's chord length
    and the distance from the center of the chord to the centerpoint of the arc.
    Formula from my favorite chord reference site: https://www.cuemath.com/geometry/Chords-of-a-circle/

    Haven't tested or proven this at all, probably won't use it.
*/
function RadFromChordLen(dist, length)
    /*
    A bit of algebra
    chord len = 2*sqrt(r^2 - d^2)
    len = 2*sqrt(r^2 - d^2)
    len/2 = sqrt(r^2 - d^2)
    (len/2)^2 = r^2 - d^2
    (len/2)^2 + d^2 = r^2
    r^2 = (len/2)^2 + d^2
    r = sqrt((len/2)^2 + d^2)
    */
    = sqrt((length/2)^2 + dist^2);
//

/*
    Calculates the length of a chord given the radius of the chord
    and the angle the chord spans across
    Formula from my favorite chord reference site: https://www.cuemath.com/geometry/Chords-of-a-circle/
*/
function ChordLenFromRadAndAngle(rad, angle) = 2*rad*sin(angle/2);
//

/*
    Given the length of the chord and the radius of the arc, determine
    how far away the chord must be from the centerpoint of the arc

    This has been tested and proven to be working correctly
*/
function ChordDistFromRad(chordLen, rad) = ((1/2)*sqrt(4*rad^2 - chordLen^2));
//

/*
    Calculates the number of points an arc of a given angle should have to best match
    a circle with the same radius.
*/
function CalculateNumberOfPointsInArc(angle) =
    let(
        /*
            Arc needs 1 more point than the circle that it is recreating would need.
            
            Arc needs n + 1 points, n points to cover the arc, and the +1 to plot the
            endpoint. Otherwise, for a given angle, arc will have one less line segment
            than an equivalently sized circle would have to cover the same area.
        */
        numPtsCalculated = ceil(angle*($fn / 360)),
        numPts = ((numPtsCalculated < 2) ? 2 : numPtsCalculated + 1)
    ) numPts;
//

// ========== Drawing 2D Geometry and Building 3D Geometry ==========
// ===== 3D Geometry =====
/*
    Converts smoothly between the provided profiles using the skin function

    Notes: 
        * Module only performs basic checks to verify that profiles are compatible
        * If input profiles are regions they must be 1 region (i.e. they can't have any holes)
        * The transformations applied to both profiles are applied relative to module's
            origin: [0, 0, 0]
        * Rotations are applied first, then translations. This causes all rotations to be
            performed relative to the center of the profile. It also means that translations
            don't what the rotations do
        * Translations are in units, rotations are in degrees

    profile1 : region or path to use for the first profile
    profile2 : region or path to use for the second profile
    profile1Translation : [x, y, z] translation to apply to profile1
    profile1Rotation : [roll, pitch, yaw] rotation to apply to profile1 assuming +x is
        forward (+roll means drop the right side, +pitch means nose down, +yaw means nose
        left, as based on default BOSL2 rot() behavior)
    profile2Translation : [x, y, z] translation to apply to profile2
    profile2Rotation : [roll, pitch, yaw] rotation to apply to profile2 assuming +x is
        forward (+roll means drop the right side, +pitch means nose down, +yaw means nose
        left, as based on default BOSL2 rot() behavior)
    scooch : small offset used to prevent profiles from intersecting if no transformation or
        rotation is applied to either

    https://github.com/BelfrySCAD/BOSL2/wiki/skin.scad#functionmodule-skin
    conversionSampling : sampling used for skin method ("length" or "segment" : only
        applicable if conversionMethod is "direct" or "reindex", both are based on
        subdivide_path() - "length" will add points along the path proportionally to the
        length of each segment length, segment adds the same number of points to each line
        segment)
    conversionMethod : method used by skin function for connecting profiles ("direct",
        "reindex", "distance", "fast_distance", or "tangent")
    conversionCenterpoint : centerpoint used by the skin function ("centroid", "mean", "box",
        or a 3D point)
    conversionResolution : number of slices to use for the skin operation (defaults to $fn)
*/
module BuildProfileConversion(profile1, profile2,
    profile1Translation = [5,5,5], profile1Rotation = [0,0,0],
    profile2Translation = [-5,-5,-5], profile2Rotation = [0,0,0],
    scooch = 0.01, conversionSampling = "length", conversionMethod = "reindex",
    conversionCenterpoint = "centroid", conversionResolution = 360/$fa,
    anchor="origin",spin=0, orient=UP, atype="hull" 
    ) {
    // --- Accounting for various types of inputs ---
    // Processing profile1
    isProfile1Path = is_path(profile1);
    isProfile1Region = is_region(profile1);
    assert(isProfile1Path || isProfile1Region, "profile1 must be a path or a region");

    // profile1 is a region, convert it back into a path
    isProfile11Region = is_1region(profile1);

    profile1ConvertedRegion = isProfile11Region ? force_path(profile1) : [];
    path1 = isProfile1Path ? profile1 : profile1ConvertedRegion;

    // Processing profile2
    isProfile2Path = is_path(profile2);
    isProfile2Region = is_region(profile2);
    assert(isProfile2Path || isProfile2Region, "profile2 must be a path or a region");

    // profile2 is a region, convert it back into a path
    isProfile21Region = is_1region(profile2);

    profile2ConvertedRegion = isProfile21Region ? force_path(profile2) : [];
    path2 = isProfile2Path ? profile2 : profile2ConvertedRegion;
    
    // --- Building the Shape that Converts between the Profiles ---
    // This uses list comprehension do to its wizardry
    // Create the outer portion of the venting shroud / duct
    skin(
        [move([0,0,scooch],
            p=move(profile1Translation,
                p=rot(profile1Rotation,
                    p=path3d(path1)))),
        move([0,0,-scooch], // Move to correct offset
            p=move(profile2Translation,
                p=rot(profile2Rotation,
                    p=path3d(path2))))],
        slices = conversionResolution, sampling = conversionSampling, method = conversionMethod,
        cp = conversionCenterpoint,
        anchor=anchor, spin=spin, orient=orient, atype=atype) children();
}

/*
    Additive version of rounding_hole_mask() in BOSL2

    r : inner radius or mask
    d : inner diameter of mask
    rounding : radius of fillet
    excess : amount of extra material to ensure proper unions
*/
module AdditiveRoundingHoleMask(r, d, rounding, excess = 0.1,
    anchor = CENTER, spin = 0, orient = UP) {
    assert(is_def(r) || is_def(d), "Either r or d must be specified");
    assert(XOR(is_def(r),is_def(d)), "Both r and d can not be specified at the same time");
    if (is_def(r))
        assert((r > 0) || is_def(d), "r must be greater than 0");
    if (is_def(d))
        assert((d > 0) || is_def(r), "d must be greater than 0");
    assert(is_def(rounding), "rounding must be defined");
    assert(rounding > 0, "rounding must be greater than 0");
    assert(excess > 0, "excess must be greater than 0");

    translationRadius = is_def(r) ? r : d/2;
    roundingRegion = right(translationRadius,
        p = zrot(90/2,
            p = GenerateCornerRoundingRegion(radius = rounding, angle = 90,
                legExtrusion = excess
            )
        )
    );

    attachmentRadius = translationRadius + rounding;
    attachable(anchor, spin, orient, r = attachmentRadius, h = rounding) {
        down(rounding/2)
        rotate_sweep(roundingRegion);

        children();
    }
}

/*
    Creates an extruded, C shaped clip.
*/
module BuildClip(innerRadius, wallThickness, span, angle = 270, cornerRounding = 0.001) {
    /*
    Arc needs 1 more point than the circle that it is recreating would need.
    Arc needs n + 1 points, n points to cover the arc, and the +1 to plot the endpoint.
    Otherwise, for a given angle, arc will have one less line segment than an equivalently
    sized circle would have to cover the same area.
    */
    numPtsCalculated = ceil(angle*($fn / 360));
    numPts = ((numPtsCalculated < 2) ? 2 : numPtsCalculated + 1);

    pieRad = innerRadius;

    outerArcPath = arc(r = pieRad + wallThickness - get_slop(), n = numPts, angle = angle);
    innerArcPath = arc(r = pieRad + get_slop(), n = numPts, angle = angle);
    endCapPath = [innerArcPath[0], outerArcPath[0]];
    clipFacePath = concat(reverse(innerArcPath), endCapPath, outerArcPath);

    clipFaceRegion = make_region(clipFacePath);
    
    // Extracting Corner Locations
    outerCorner1 = outerArcPath[0];
    outerCorner2 = last(outerArcPath);
    innerCorner1 = innerArcPath[0];
    innerCorner2 = last(innerArcPath);

    corners = concat([outerCorner1], [outerCorner2], [innerCorner1], [innerCorner2]);
    echo("Corners : ", corners);

    // Extracting Rounding Angles
    /*
    "Perfect" Rounding of Corners
    I want to round the corners on this shape perfectly, but it'd difficult to do since
    the shape can change drastically depending on $fn.
    However, I've figured out now to do it.
    The edges of the clip are always co-linear with the centerpoint of the clip, which means
    the ideal rounding angle is always around 90 deg.
    That means that a line can be created at a 45 deg angle from the face edge, and
    it's intersection point with the polygon can be used to determine the true rounding angle.
    
    Note: The inner and outer corners have slightly different angles, which both are
        and are not complimentary. They are complimentary in that, were this not a circular
        shape with thickness, the values would be complimentary. However, because this is a
        circular shape with a thickness, the interior value (it seems like the problem appears
        because of concave curvature) will be slightly greater than the complimentary angle.
        

    Constructing references for corner 1 for both corners because they are the easiest
    to work with, both of them being on the x axis.
    Steps:
    1. Generate Arc (completed above)
    2. Determine point on clip edge at proper distance from edge (rounding radius)
    3. Construct line at a 45 degree angle from that
    4. Determine where that line intersects with the polygon (bounded solution, to restructure the number
        of solutions to 2)
    5. Use those points and the corner-location to construct a corner path
    6. Use the vector_angle to determine the angle of said corner
    7. Construct corner rounding region with proper angle
    8. Repeat Steps 2-7 for interior angle
    */
    
    // 2. Determining point on edge that is proper distance in from edge
    outerCornerIntersectionLineEndpoint1 = outerCorner1 - [cornerRounding, 0];
    
    // 3. Constructing Line at 45 Degree Angle
    // Because the angle is 45 degrees no trig is required, can just add the same constant amount to x and y
    outerCornerIntersectionLineEndpoint2 = outerCornerIntersectionLineEndpoint1 + [wallThickness*2, wallThickness*2];
    outerCornerIntersectionLine = [outerCornerIntersectionLineEndpoint1, outerCornerIntersectionLineEndpoint2];

    // 4. Determine where line intersects polygon
    // Intersections in 2d return a mixture of points and line-segments, but
    // this has been planned to force the solution to be a single line segment
    outerCornerClipIntersection = polygon_line_intersection(poly = clipFacePath, line = outerCornerIntersectionLine, bounded = true);
    // Intersection is a list of paths and lines, but since there is only one result, it can be accessed
    // simply by removing one array level
    outerCornerClipIntersectionLineSegment = flatten(outerCornerClipIntersection);
    
    // 5. Constructing Corner for vector_angle()
    outerCorner1SegmentEndpoint1 = outerCornerClipIntersectionLineSegment[0];
    outerCorner1SegmentEndpoint2 = outerCornerClipIntersectionLineSegment[1];
    outerCornerVectorAnglePath = concat([outerCorner1SegmentEndpoint1], [outerCorner1], [outerCorner1SegmentEndpoint2]);
    
    // 6. Using vector_angle() to calculate the angles
    outerCornerRoundingAngle = vector_angle(outerCornerVectorAnglePath);

    // 7. Constructing Corner Rounding Regions with Calculated Angle
    // Rounding Outer Corners
    outerCorner1Region = move(outerCorner1,
        zrot(-(outerCornerRoundingAngle/2) + 180,
            p=GenerateCornerRoundingRegion(radius = cornerRounding, angle = outerCornerRoundingAngle, legExtrusion=wallThickness/4)));
    outerCorner2Region = move(outerCorner2,
        zrot((outerCornerRoundingAngle/2) + 180 + angle,
            p=GenerateCornerRoundingRegion(radius = cornerRounding, angle = outerCornerRoundingAngle, legExtrusion=wallThickness/4)));
    
    clipFaceOuterRoundedRegion = difference(clipFaceRegion, outerCorner1Region, outerCorner2Region);
    
    // Rounding Inner Corners
    // 2. Determining point on edge that is proper distance in from edge
    innerCornerIntersectionLineEndpoint1 = innerCorner1 + [cornerRounding, 0];
    
    // 3. Constructing Line at an Angle to Polygon (initially 45 Degrees)
    /*
    Being a bit fancy about this. There are some scenarios where the naive rounding
    method (assuming the angle is 45 degrees) works well, and other's where it doesn't.
    If the naive method finds a solution, then that's the solution that will be used.
    However, if the naive method can't find a solution, then the more advanced method
    (i.e. the pretty looking duct tape fix) will be used. The more advanced method takes
    the amount the outer angle was off from 90 degrees, and adds that to the default
    45 degree angle for computing the line.

    */
    // Because the angle is 45 degrees no trig is required, can just add the same constant amount to x and y    
    innerLineOffset = (pieRad + get_slop())*sqrt(2); // Diagonal of a square with a side length equal to the radius of the inner arc
    innerCornerIntersectionLineEndpoint2 = innerCornerIntersectionLineEndpoint1 + [-innerLineOffset*cos(45), innerLineOffset*sin(45)];
    innerCornerIntersectionLine = [innerCornerIntersectionLineEndpoint1, innerCornerIntersectionLineEndpoint2];

    outerDifferenceFrom90 = abs(90 - outerCornerRoundingAngle);
    innerFancyLineAngle = 45 - outerDifferenceFrom90;
    innerCornerFancyIntersectionLineEndpoint2 = innerCornerIntersectionLineEndpoint1 + [-innerLineOffset*cos(innerFancyLineAngle), innerLineOffset*sin(innerFancyLineAngle)];
    innerCornerFancyIntersectionLine = [innerCornerIntersectionLineEndpoint1, innerCornerFancyIntersectionLineEndpoint2];

    // 4. Determine where line intersects polygon
    // Intersections in 2d return a mixture of points and line-segments, but
    // this has been planned to force the solution to be a single line segment
    innerCornerClipIntersection = polygon_line_intersection(poly = clipFacePath, line = innerCornerIntersectionLine, bounded = true);
    // Intersection is a list of paths and lines, but since there is only one result, it can be accessed
    // simply by removing one array level
    innerCornerClipIntersectionLineSegment = flatten(innerCornerClipIntersection);
        
    innerCornerFancyClipIntersection = polygon_line_intersection(poly = clipFacePath, line = innerCornerFancyIntersectionLine, bounded = true);
    innerCornerFancyClipIntersectionLineSegment = flatten(innerCornerFancyClipIntersection);
    
    // 5. Constructing Corner for vector_angle()
    /*
    Which line segment we use depends on whether or not the naive approach failed.
    When the naive approach fails, it returns the same line segment as the one passed
    into polygon_line_intersection().
    */
    
    innerCornerIntersectionLineFullyFlattened = full_flatten(innerCornerIntersectionLine);
    innerCornerClipIntersectionLineSegmentFullyFlattened = full_flatten(innerCornerClipIntersectionLineSegment);
    // compare_lists() returns 0 if they are identical, neg numbers if first less less than second, and pos numbers if first is greater than second
    lineComparison = compare_lists(innerCornerIntersectionLineFullyFlattened, innerCornerClipIntersectionLineSegmentFullyFlattened);
    didNaiveTestFail = (lineComparison == 0);

    echo("Naive Intersection Line   : ", innerCornerIntersectionLine);
    echo("Naive Intersection Result : ", innerCornerClipIntersectionLineSegment);
    echo("Did Naive Fail : ", didNaiveTestFail);

    innerCorner1SegmentEndpoint1 = didNaiveTestFail ? innerCornerFancyClipIntersectionLineSegment[0] : innerCornerClipIntersectionLineSegment[0];
    innerCorner1SegmentEndpoint2 = didNaiveTestFail ? innerCornerFancyClipIntersectionLineSegment[1] : innerCornerClipIntersectionLineSegment[1];
    innerCornerVectorAnglePath = concat([innerCorner1SegmentEndpoint1], [innerCorner1], [innerCorner1SegmentEndpoint2]);
    
    // 6. Using vector_angle() to calculate the angles
    innerCornerRoundingAngle = vector_angle(innerCornerVectorAnglePath);

    innerCorner1Region = move(innerCorner1,
        zrot((innerCornerRoundingAngle/2),
            p=GenerateCornerRoundingRegion(radius = cornerRounding, angle = innerCornerRoundingAngle, legExtrusion=wallThickness/4)));

    innerCorner2Region = move(innerCorner2,
        zrot(-(innerCornerRoundingAngle/2) + 0 + angle,
            p=GenerateCornerRoundingRegion(radius = cornerRounding, angle = innerCornerRoundingAngle, legExtrusion=wallThickness/4)));

    clipFaceRoundedRegion = difference(clipFaceOuterRoundedRegion, innerCorner1Region, innerCorner2Region);

    // --- Finally Making the Clip ---
    linear_sweep(region = clipFaceRoundedRegion, height = span);
}

/*
    Module that uses the Fibonacci Sphere Algorithm to place small spheres on the surface
    of a larger sphere.

    Just a random idea I had. A while ago I figured out the formula to create a circle
    with an arbitrary number of points, and I've always wondered how to do that for a
    sphere.

    Code based on the python provided at this link:
    https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere
*/
module BuildFibonacciSphere(numPoints, sphereRadius = 1, dotRadius = 0.05) {
    points = CalculateFibonacciSphereDistribution(numPoints=numPoints, sphereRadius=sphereRadius);
    
    // move_copies(points) spheroid(r = dotRadius, style = "icosa", $fn = 5);
    move_copies(points) spheroid(r = dotRadius);
}

/*
    Creates a more or less even distribution of points on the face of a sphere using the
    Fibonacci Sphere Algorithm

    Just a random idea I had. A while ago I figured out the formula to create a circle
    with an arbitrary number of points, and I've always wondered how to do that for a
    sphere.

    Code based on the python provided at this link:
    https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere
*/
function CalculateFibonacciSphereDistribution(numPoints, sphereRadius = 1) =
    let(
        // Golden angle in radians
        goldenAngle = PI * PHI,

        // Using list comprehension to generate the points on the surface of the sphere
        points = [for (i = [1:1:numPoints])
            let(
                y = 1 - (i / numPoints)*2, // Clamping y between -1 and 1
                radius = sqrt(1 - y*y),

                // Golden Angle Increment
                theta = goldenAngle*i,

                radiansToDegreesConversionConstant = 180/PI,

                x = cos(theta*radiansToDegreesConversionConstant)*radius,
                z = sin(theta*radiansToDegreesConversionConstant)*radius,

                point = [x, y, z])
            point],
            fibonacciSpherePoints = scale(sphereRadius, p = points)
    ) fibonacciSpherePoints;
// 

/*
    Connects two spheres with a curved waist. 3D version of the BOSL2 2d geometry
    glued_circles. 

    r : radius of the spheres
    spread : distance between the center points of the spheres
    tangent : angle in degrees of the tangent for the joining arcs
*/
module BuildGluedSpheres(r, spread, tangent) {
    gluedCircles = glued_circles(r = r, spread = spread,
        tangent = tangent);
    gluedCirclesRegion = make_region(gluedCircles);

    // Slice gluedCircles along x-axis
    // Creating Trimming Shape
    trimmingBoxDimensions = [2*r + spread, r];
    trimmingBoxProfile = rect(trimmingBoxDimensions);
    trimmingBox = move([0, -trimmingBoxDimensions.y/2], p = trimmingBoxProfile);
    trimmingBoxRegion = make_region(trimmingBox);

    // Trimming Profiles
    gluedHemispheresRegion = difference(gluedCirclesRegion, trimmingBoxRegion);

    gluedHemispheresProfile = force_path(gluedHemispheresRegion);
    
    // Creating 3d Geometry
    gluedSpheres = zrot(-90, gluedHemispheresProfile);

    yrot(90) // To match orientation of glued_circles()
    rotate_sweep(gluedSpheres, angle = 360);
}

/*
    Connects two cylinders with a curved waist. Extruded version of BuildGluedSpheres

    r : radius of the spheres
    spread : distance between the center points of the cylinders
    length : length / height of the cylinders
    tangent : angle in degrees of the tangent for the joining arcs
    roundEnds : if false, ends will be planar, if true, ends will be rounded (adds
        additional length)
*/
module BuildGluedCylinders(r, spread, length, tangent, roundEnds = true) {
    cylinderPath = [[length/2,0], [-length/2,0]];
    
    yrot(90) // To match orientation of BuildGluedSpheres
    path_extrude2d(cylinderPath, caps = roundEnds)
    zrot(90)
    glued_circles(r = r, spread = spread, tangent = tangent);
}

/*
    Constructs a cuboid with chamfers applied to the top and bottom faces, but rounding
    applied to the vertical edges.

    Name inspired by Slant3D, who recommends you make all parts this shape which is really
    good for mass production 3d printing
    
    dimensions : [x, y, z] dimensions of the cuboid
    chamfer : chamfer to the top and bottom faces
    verticalRounding : rounding to apply to the vertical edges (if -1, chamfer value will be
        applied, behavior changed to joint if makeVerticalRoundingSmooth is true, joint is the
        distance inwards from the corner at which the transition begins)
    makeVerticalRoundingSmooth : if true, rounds the corners using the smooth function
    smoothVerticalRoundingK : k value to use for smooth rounding (0.7 by default to make
        joint and radius effects similar)
*/
module BuildMassProductionCuboid(dimensions, chamfer, verticalRounding = -1,
    makeVerticalRoundingSmooth = false, smoothVerticalRoundingK = 0.5) {
    rounding = (verticalRounding == -1) ? chamfer : verticalRounding;
    
    // Create the outline for the offset sweep
    sharpOutline = rect([dimensions.x, dimensions.y]);
    outline = makeVerticalRoundingSmooth
        ? round_corners(sharpOutline, joint = rounding, method = "smooth", k = smoothVerticalRoundingK,
            closed = true)
        : round_corners(sharpOutline, radius = rounding, closed = true);

    // Build the shape using offset sweep
    offsetProfile = os_chamfer(height = chamfer);
    offset_sweep(outline, height = dimensions.z, bottom=offsetProfile, top=offsetProfile);
}

// ===== 2D Geometry =====
/*
    Creates a region that can be used to round corners to a desired radius.
    Intended to be used by taking the difference of the original geometry and
    the region created to round the corner.

    radius : radius to make the corner
    angle : angle of the corner
    legExtrusion : extra material extending from the ends of the legs (for difference
        operations)
*/
module DrawCornerRoundingRegion(radius=10, angle=90, legExtrusion=5) {
    regionToBuild = GenerateCornerRoundingRegion(radius=radius, angle=angle, legExtrusion=legExtrusion);
    region(regionToBuild);
}

/*
    Returns a region that can be used to round corners to a desired radius.
    Intended to be used by taking the difference of the original geometry and
    the region created to round the corner.
    Angles can be specified, but the default angle is 90 deg.

    radius : radius to make the corner
    angle : angle of the corner
    legExtrusion : extra material extending from the ends of the legs (for difference
        operations)
*/
function GenerateCornerRoundingRegion(radius=10, angle=90, legExtrusion=5) = 
    let(
        /*
        Now that I have the proper side length, is pretty simple to do the rest
        of this.
        It's going to take a lot of code cleanup though.
        
        Simplified Steps:
        1. Create Unit Angle - this is used to generate the proper chord
        2. Determine Chord - just an arc with n=2
        3. Determine side length - that's isoSideLen, basic trig stuff
        4. Use new side length to create actual rounding corner feature
        5. Fill interior of rounding corner arc - create a region
        6. Extrude out legs of rounding corner - extrude path to create a region
        7. Merge both features to create the difference geometry - performed using regions
        8. Translate Shape to Proper Position
            Assuming the arc is a perfect circle, when no transformations are applied the origin
            should line up with the point on the circle that is the closest to the centerpoint of
            the outer triangle thing.
            Should probably also be rotated so that the +X axis bisects the angle being rounded over
        */
        
        /*
        $fn is the number of fragments in a circle
        $fn / 360 = n / ang
        ($fn / 360) = n / ang
        ang * ($fn / 360) = n
        */

        /*
        Arc needs 1 more point than the circle that it is recreating would need.
        Arc needs n + 1 points, n points to cover the arc, and the +1 to plot the endpoint.
        Otherwise, for a given angle, arc will have one less line segment than an equivalently
        sized circle would have to cover the same area.
        */
        numPtsCalculated = ceil(angle*($fn / 360)),
        numPts = ((numPtsCalculated < 2) ? 2 : numPtsCalculated + 1),
        roundingArcPts = numPts,

        pieRad = radius,
        extrusionAmount = legExtrusion,
        
        /*
        The arc function provides an easy way to generate a geometry that will
        properly sweep over the corner without having to do trig.
        That and I started with this, then realized it had the wrong concavity
        only after figuring out the rest of the details (but realized that this
        is still the best way to go, because you can determine the length of the
        arc chord by generating an arc with only 2 points, i.e. a line segment)
        
        I could go down the rabbit hole of how to solve this, or just use the built in features
        that I have.
        I tracked down the function that does this wizardry, but I don't understand why
        those functions work, at least I think this is the function responsible for solving
        this problem.
        https://github.com/BelfrySCAD/BOSL2/wiki/geometry.scad#function-circle_2tangents
        */
        // 1. This is a unit arc
        unitArcPath = arc(n=2, r=1, angle=angle, wedge=true),
        
        /*
        Path format for arc, [i=0, origin/corner], [i=1, endpoint of 1st leg], ..., [i=n-1, endpoint of 2nd leg]
        Extract points of required for modeling legs, and create path with those
        */

        /*
        Creating a unit corner from the reference 
        */
        cornerPoint = unitArcPath[0],
        firstLegEndpoint = unitArcPath[1],
        secondLegEndpoint = last(unitArcPath), // Easier way to pull the last index
        unitCornerPath = [secondLegEndpoint, cornerPoint, firstLegEndpoint],
        
        // 2. Determine Chord Length
        chordLinePath = arc(corner=unitCornerPath, n=2, r = pieRad),
        chordLength = CalculatePointDistance(chordLinePath[0], chordLinePath[1]),
        isoAngle = (180 - angle)/2,
                
        // 3. Determine Side Length of Isosceles Triangle
        // Have to label the inputs to get this to work properly
        isoSideLen = law_of_sines(a=chordLength, A=angle, B=isoAngle),
        
        // 4. Constructing Actual Corner
        // Again, being clever and making arc do the heavy lifting
        roundingCornerArcPath = arc(n=2, r=isoSideLen, angle=angle, wedge=true),
        roundingCornerCenterpoint = roundingCornerArcPath[0],
        roundingCornerFirstLegEndpoint = roundingCornerArcPath[1],
        roundingCornerSecondLegEndpoint = last(roundingCornerArcPath),
        roundingCornerPath = [roundingCornerSecondLegEndpoint, roundingCornerCenterpoint, roundingCornerFirstLegEndpoint],
        
        roundingArcPath = arc(corner=unitCornerPath, n=roundingArcPts, r = pieRad),
        
        // 5. Fill Interior of Rounding Corner
        
        roundingCornerInteriorPath = concat(roundingCornerPath, reverse(roundingArcPath)),
        roundingCornerInteriorRegion = make_region(roundingCornerInteriorPath),
        
        // 6. Take Offset of Rounding Corner Legs
        roundingCornerOffsetPath = offset(roundingCornerPath, delta = -extrusionAmount, same_length = true, closed = false),
        
        // Final segment, goes from the end of the offset to the start of the initial path
        closingLeg = [roundingCornerOffsetPath[0], roundingCornerPath[0]],
        legExtrusionPath = concat(roundingCornerPath, reverse(roundingCornerOffsetPath), closingLeg),
        legExtrusionRegion = make_region(legExtrusionPath),
                
        // 7. Join Features
        
        cornerRoundingRegion = union(roundingCornerInteriorRegion, legExtrusionRegion),
        
        /*
        8. Translate to Easy to Understand Origin
        It would make the most sense to have the origin of this shape be located
        such that you wouldn't have to apply any translations to round a corner, only
        rotation.
        Also, default angle should bisect the +X axis. This seems the most logical, as
        it requires a predictable amount of correction no matter which way it needs rotated.
        */
        
        // Again, it is possible to make BOSL do the heavy lifting
        // originExtractionArcPath = arc(corner=unitCornerPath, n=3, r = pieRad),
        // originPoint = originExtractionArcPath[1], // Path of 3, must be middle point
        originPoint = cornerPoint,
        
        // The corner the rounding arc fills is the exact corner we are rounding,
        // That is our rounding reference
        regionPath = zrot(-angle/2, p=
            move(-originPoint, p=cornerRoundingRegion)),
        
        returnRegion = make_region(regionPath)
        )
        returnRegion;
//

/*
    Generates an arc with a given radius that is bounded by the specified endpoints

    pt1 : one corner endpoint
    pt2 : the other corner endpoint
    pts : list of two points
    radius : radius of the arc
    flip : controls which side of the corner the arc is generated on (can be used to toggle
        between interior and exterior corner rounding)
*/
function GenerateArcWithEndpoints(pt1, pt2, pts, radius, flip = false) =
    let(
        centerpoint = CalculateArcCenterpointFromEndpoints(pt1 = pt1, pt2 = pt2, pts = pts,
            radius = radius, flip = flip),
        arc = arc(r = radius, cp = centerpoint, points = [pt1, pt2])
    ) arc;
//

/*
    Calculates the centerpoint of an arc with a given radius that is bounded by the
        specified endpoints

    pt1 : one corner endpoint
    pt2 : the other corner endpoint
    pts : list of two points
    radius : radius of the arc
    flip : controls which side of the corner the arc is generated on (can be used to toggle
        between interior and exterior corner rounding)
*/
function CalculateArcCenterpointFromEndpoints(pt1, pt2, pts, radius, flip = false) =
    assert(is_def(pt1) || is_def(pt2) || is_def(pts), "Provide pt1 and pt2 or pts")
    assert(is_undef(pts) || (is_path(pts,[2]) && len(pts) == 2))
    assert(is_undef(pt1) || is_undef(pt2) || is_undef(pts), "Cannot specify individual points and a list of points.")
    assert(is_undef(pt1) || is_undef(pts), "Cannot specify individual points and a list of points.")
    assert(is_undef(pt2) || is_undef(pts), "Cannot specify individual points and a list of points.")
    assert((is_def(pt1) && is_def(pt2)) || is_path(pts), "Both pt1 and pt2 must be defined")
    let(
        /*
            Given any two points, I want to figure out how to draw a circle that will be tangent
            to them

            Know:
            Circle EQ: (x-cp_x)^2 + (y-cp_y)^2 = r^2

            Figured it out by tinkering in Desmos: https://www.desmos.com/calculator/u9wgtqhxwr

            Steps:
            1. Use circle_circle_intersection to determine where said circles intersect
            2. Either of the two intersection points can be the centerpoint, choose one
        */
        providedPts = is_path(pts),
        cp1 = providedPts ? pts[0] : pt1,
        cp2 = providedPts ? pts[1] : pt2,

        potentialCenterpoints = circle_circle_intersection(r1 = radius, r2 = radius,
            cp1 = cp1, cp2 = cp2),
        centerpoint = flip ? potentialCenterpoints[0] : potentialCenterpoints[1]
    ) centerpoint;
//

// ===== 3D Filleted Edge and Masking Suite Development =====
if (false) {
    edgeLen = 10;
    sideRad = 3;
    edgeRad = 4;
    internalOffset = 2;

    // render()

    // ExternalConvexFilletedCornerMask(rad = sideRad, internalOffset = internalOffset);
    // ExternalConcaveFilletedCornerMask(rad = sideRad, internalOffset = internalOffset);
    // InternalConvexFilletedCornerMask(rad = sideRad, internalOffset = internalOffset);
    // InternalConcaveFilletedCornerMask(rad = sideRad, internalOffset = internalOffset);


    // BuildExternalConvexFilletedEdge(totalEdgeLength = edgeLen, sideRad = sideRad, edgeRad = edgeRad);
    // BuildExternalConcaveFilletedEdge(totalEdgeLength = edgeLen, sideRad = sideRad, edgeRad = edgeRad);
    // BuildInternalConvexFilletedEdge(totalEdgeLength = edgeLen, sideRad = sideRad, edgeRad = edgeRad);
    // BuildInternalConcaveFilletedEdge(totalEdgeLength = edgeLen, sideRad = sideRad, edgeRad = edgeRad);
}

// === 3D Filleted Corner Masks ===

/*
    3D corner mask to be applied to convex outer corners between edges where two edges share
    one radius while the third edge has a different radius

    Note: Outer radius = rad + internalOffset

    rad : radius of fillet on the corner masks that transitions between the two radii
    internalOffset : radius of the smaller edge, also the offset from the origin before
        the fillet begins (0 makes the end perfectly round)
*/
module ExternalConvexFilletedCornerMask(rad = 1, internalOffset = 1) {
    
    maskFootprint = [rad + internalOffset + 0.02, rad + internalOffset + 0.02, rad];
    
    difference() { // Begin Curvature Reversal Difference
        // Cubiod for most of the area
        up(maskFootprint[2]/2)
        back(maskFootprint[1]/2 + 0.01)
        right(maskFootprint[0]/2 + 0.01)
        cuboid(maskFootprint);
        
        // Cylinder to get rid of texture fighting along the main axis
        up(rad/2)
        zcyl(h = rad*2, r = internalOffset);
        
        InternalConcaveFilletedCornerMask(rad = rad, internalOffset = internalOffset);
    } // End Curvature Reversal Difference
}

/*
    3D corner mask to be applied to concave outer corners between edges where two edges share
    one radius while the third edge has a different radius

    Note: Outer radius = rad + internalOffset

    rad : radius of fillet on the corner masks that transitions between the two radii
    internalOffset : radius of the smaller edge, also the offset from the origin before
        the fillet begins (0 makes the end perfectly round)
*/
module ExternalConcaveFilletedCornerMask(rad = 1, internalOffset = 1) {
    rotate_extrude(angle = 90) { // Begin Rotate Extrude
        union() { // Begin 2d profile union
            right(internalOffset)
            right(rad)
            back(rad)
            mask2d_roundover(r = rad, spin = 180);
        } // End 2d profile union
    }  // End Rotate Extrude
    
    difference() { // Begin Corner Filling Difference
        maskFootprint = [rad + internalOffset, rad + internalOffset, rad];
        
        back(maskFootprint[1]/2)
        right(maskFootprint[0]/2)
        up(maskFootprint[2]/2)
        cuboid(maskFootprint);
        
        // Cutting out a space for the mask to fill
        zcyl(r = rad + internalOffset - 0.01, h = 3*rad);
        
    } // End Corner Filling Difference
}

/*
    3D corner mask to be applied to convex inner corners between edges where two edges share
    one radius while the third edge has a different radius

    Note: Outer radius = rad + internalOffset

    rad : radius of fillet on the corner masks that transitions between the two radii
    internalOffset : radius of the smaller edge, also the offset from the origin before
        the fillet begins (0 makes the end perfectly round)
*/
module InternalConvexFilletedCornerMask(rad = 1, internalOffset = 1) {
    
    maskFootprint = [rad + internalOffset - 0.01, rad + internalOffset - 0.01, rad];
    
    difference() { // Begin Curvature Reversal Difference
        up(maskFootprint[2]/2)
        back(maskFootprint[1]/2 + 0.005)
        right(maskFootprint[0]/2 + 0.005)
        cuboid(maskFootprint);
        
        // Fillet to get rid of texture fighting at the top and bottom
        up(rad/2)
        right(internalOffset + rad)
        back(internalOffset + rad)
        fillet(l = rad*2, r = internalOffset + rad, spin = 180);
        
        ExternalConcaveFilletedCornerMask(rad = rad, internalOffset = internalOffset);
    } // End Curvature Reversal Difference
    
}

/*
    3D corner mask to be applied to concave inner corners between edges where two edges share
    one radius while the third edge has a different radius

    Note: Outer radius = rad + internalOffset

    rad : radius of fillet on the corner masks that transitions between the two radii
    internalOffset : radius of the smaller edge, also the offset from the origin before
        the fillet begins (0 makes the end perfectly round)
*/
module InternalConcaveFilletedCornerMask(rad = 1, internalOffset = 1) {
    rotate_extrude(angle = 90) { // Begin Rotate Extrude
        union() { // Begin 2d profile union
            right(internalOffset)
            mask2d_roundover(r = rad);
            
            square([internalOffset, rad]); //to fill in the middle
        } // End 2d profile union
    }  // End Rotate Extrude
}

// === 3D Filleted Edges with Transitions ===
/*
    Straight 3D edge geometry that generates square corners (see note). Generates correct
    geometry for a convex, filleted edge for an outer corner.
    
    To be used in situations where an edge should be filleted with one radius, but all other
    intersecting edges have a different, shared radius

    Note: Use only for corners where all intersecting edges are perpendicular to each other

    totalEdgeLength : length of the entire edge (termination point to termination point)
    sideRad : fillet radii of all other intersecting edges
    edgeRad : fillet radius of the majority of the edge (the one unique radius)
*/
module BuildExternalConvexFilletedEdge(totalEdgeLength = 8, sideRad = 2, edgeRad = 3) {
    
    filletLength = totalEdgeLength - 2*sideRad;

    filletSliceFootprint = [sideRad, filletLength + 0.01, sideRad + edgeRad];
    
    union() { // Begin Edge Creation Union
        
        right(sideRad)
        up(sideRad)
        fillet(l = filletLength + 0.01, r = edgeRad, orient = FRONT);
        
        // Cuboids to fill in space under fillet
        right(filletSliceFootprint[0]/2)
        up(filletSliceFootprint[2]/2)
        cuboid(filletSliceFootprint);
        
        MirrorXY(duplicateObject = false)
        yrot(90)
        right(filletSliceFootprint[0]/2)
        up(filletSliceFootprint[2]/2)
        cuboid(filletSliceFootprint);
        
        minorEdgeRad = edgeRad - sideRad;
        
        MirrorXZ()
        right(sideRad + edgeRad)
        fwd(filletLength/2 + sideRad)
        up(sideRad + edgeRad)
        yflip()
        yrot(180)
        xrot(90)
        ExternalConvexFilletedCornerMask(rad = sideRad, internalOffset = edgeRad);
    } // End Edge Creation Union
}

/*
    Straight 3D edge geometry that generates square corners (see note). Generates correct
    geometry for a concave, filleted edge for an outer corner.
    
    To be used in situations where an edge should be filleted with one radius, but all other
    intersecting edges have a different, shared radius

    Note: Use only for corners where all intersecting edges are perpendicular to each other

    totalEdgeLength : length of the entire edge (termination point to termination point)
    sideRad : fillet radii of all other intersecting edges
    edgeRad : fillet radius of the majority of the edge (the one unique radius)
*/
module BuildExternalConcaveFilletedEdge(totalEdgeLength = 8, sideRad = 2, edgeRad = 3) {
    
    filletLength = totalEdgeLength - 2*sideRad;

    edgeFootprint = [sideRad, totalEdgeLength + 0.01, sideRad + edgeRad];
    
    union() { // Begin Edge Creation Union
        
        right(sideRad)
        up(sideRad)
        fillet(l = filletLength + 0.01, r = edgeRad, orient = FRONT);
        
        // Cuboids to fill in space under geometry
        right(edgeFootprint[0]/2)
        up(edgeFootprint[2]/2)
        cuboid(edgeFootprint);
        
        MirrorXY(duplicateObject = false)
        yrot(90)
        right(edgeFootprint[0]/2)
        up(edgeFootprint[2]/2)
        cuboid(edgeFootprint);
        
        minorEdgeRad = edgeRad - sideRad;
        
        MirrorXZ()
        right(sideRad + edgeRad)
        back(filletLength/2)
        up(sideRad + edgeRad)
        yflip()
        yrot(180)
        xrot(90)
        ExternalConcaveFilletedCornerMask(rad = sideRad, internalOffset = edgeRad - sideRad);
    } // End Edge Creation Union
}

/*
    Straight 3D edge geometry that generates square corners (see note). Generates correct
    geometry for a convex, filleted edge for an inner corner.
    
    To be used in situations where an edge should be filleted with one radius, but all other
    intersecting edges have a different, shared radius

    Note: Use only for corners where all intersecting edges are perpendicular to each other

    totalEdgeLength : length of the entire edge (termination point to termination point)
    sideRad : fillet radii of all other intersecting edges
    edgeRad : fillet radius of the majority of the edge (the one unique radius)
*/
module BuildInternalConvexFilletedEdge(totalEdgeLength = 8, sideRad = 1, edgeRad = 3) {
    filletLength = totalEdgeLength - 2*sideRad;
    
    edgeFootprint = [sideRad + edgeRad - 0.01, totalEdgeLength, sideRad + edgeRad - 0.01];
    
    left(sideRad)
    down(sideRad)
    difference() { // Begin Curvature Reversal Difference
        up(edgeFootprint[2]/2 + 0.005)
        right(edgeFootprint[0]/2 + 0.005)
        cuboid(edgeFootprint);
        
        BuildExternalConcaveFilletedEdge(totalEdgeLength = totalEdgeLength, sideRad = sideRad, edgeRad = edgeRad);
        
        // Creating fillet to get rid of texture fighting
        right(sideRad)
        up(sideRad)
        fillet(l = totalEdgeLength + 0.01, r = edgeRad, orient = BACK, spin = -90);      
    } // End Curvature Reversal Difference
}

/*
    Straight 3D edge geometry that generates square corners (see note). Generates correct
    geometry for a concave, filleted edge for an inner corner.
    
    To be used in situations where an edge should be filleted with one radius, but all other
    intersecting edges have a different, shared radius

    Note: Use only for corners where all intersecting edges are perpendicular to each other

    totalEdgeLength : length of the entire edge (termination point to termination point)
    sideRad : fillet radii of all other intersecting edges
    edgeRad : fillet radius of the majority of the edge (the one unique radius)
*/
module BuildInternalConcaveFilletedEdge(totalEdgeLength = 8, sideRad = 1, edgeRad) {
    filletLength = totalEdgeLength - 2*sideRad;
    
    edgeFootprint = [sideRad + edgeRad - 0.01, totalEdgeLength, sideRad + edgeRad - 0.01];
    
    difference() { // Begin Curvature Reversal Difference
        up(edgeFootprint[2]/2 + 0.005)
        right(edgeFootprint[0]/2 + 0.005)
        cuboid(edgeFootprint);
        
        BuildExternalConvexFilletedEdge(totalEdgeLength = totalEdgeLength, sideRad = sideRad, edgeRad = edgeRad);
        
        // Creating fillet to get rid of texture fighting at ends
        fillet(l = totalEdgeLength + 0.01, r = sideRad + edgeRad, orient = BACK, spin = -90);
        
        // Using cylinders to get rid of the extra material at the filleted features
        MirrorXZ()
        back(filletLength/2)
        up((sideRad + edgeRad)/2)
        zcyl(h = sideRad + edgeRad + 0.01, r = sideRad);
        
        yrot(90)
        MirrorXZ()
        back(filletLength/2)
        up((sideRad + edgeRad)/2)
        zcyl(h = sideRad + edgeRad, r = sideRad);
    } // End Curvature Reversal Difference
}




// ========== Unfinished ==========
/*
    Draws a region with two curves of a specified radius that smoothly fillets the interior
    of one corner and the exterior of the other corner with a specified radius.

    WARNING: WORK IN PROGRESS (progress was halted to investigate the smooth rounding option
        in BOSL2)

    radius : radius of the curve to use when rounding
    spacing : distance between the corners of the squares
*/
module DrawBlendedSquareCorners(radius, spacing) {
    horizontalLegLength = min(radius, spacing/2);

    // cornerTemplate = [[0,radius],[0,0],[-radius,0]];
    cornerTemplate = [[0,radius],[0,0],[-horizontalLegLength,0]];

    // GenerateArcWithEndpoints(pt1 = cornerTemplate[0], pt2 = cornerTemplate[2], radius = radius,
    //     flip = false);

    // Finding the arc with the proper radius that fits in this corner
    arcTemplate = GenerateArcWithEndpoints(pt1 = cornerTemplate[0], pt2 = cornerTemplate[2],
        radius = radius, flip = false);

    positiveCorner = move([spacing/2, 0], p = cornerTemplate);
    negativeCorner = move([-spacing/2, 0],
        p = zrot(180, p = cornerTemplate));

    cornerPath = concat(positiveCorner, reverse(negativeCorner));

    // positiveArc = arc(r = radius, corner = positiveCorner);
    // negativeArc = arc(r = radius, corner = negativeCorner);
    positiveArc = move([spacing/2, 0], p = arcTemplate);
    negativeArc = move([-spacing/2, 0],
        p = zrot(180, p = arcTemplate));
    
    cornerArcPath = deduplicate(
                        concat(positiveArc, reverse(negativeArc)));

    echo(path_curvature(cornerArcPath));

    up(0) {
        // stroke(cornerTemplate, color = "khaki", width = 0.5,
        //     dots = true, dots_color = "black", dots_width = 1);
        // stroke(arcTemplate, color = "darkKhaki", width = 0.25);

        stroke(positiveCorner, color = "tan", width = 0.5);
        stroke(negativeCorner, color = "darkGoldenrod", width = 0.5);

        stroke(positiveArc, color = "teal", width = 0.25);
        stroke(negativeArc, color = "green", width = 0.25);
        
        stroke(cornerArcPath, color = "cyan", width = 0.1, dots = true);
        // stroke(cornerPath, color = "red", width = 0.1, dots = true, dots_color = "blue");
    }

    
}
//

// ========== Beziers and VNFs UNFINISHED ==========
/*
    Plots the provided bezier patch in debug mode, and draws each edge offset
    by the specified amount
*/
module ExtractAndPlotEdgeCurve(patch, edge, offset = 5) {
    patchDimensions = list_shape(patch);
    patchBounds = pointlist_bounds(flatten(patch));

    extractedEdgeCurve = ExtractPatchEdge(patch, edge);

    edgeToTranslationLookupStruct = struct_set([],
                        [BACK, [0, patchBounds[1].y + offset, 0],
                        FRONT, [0, patchBounds[0].y - offset, 0],
                        LEFT, [patchBounds[0].x - offset, 0, 0],
                        RIGHT, [patchBounds[1].x + offset, 0, 0]
                        ]);
    translationAmount = struct_val(edgeToTranslationLookupStruct, edge);
    
    edgeToRotationLookupStruct = struct_set([],
                        [BACK, [90, 0, 0],
                        FRONT, [90, 0, 0],
                        LEFT, [90, 0, 90],
                        RIGHT, [90, 0, 90]
                        ]);
    rotationAmount = struct_val(edgeToRotationLookupStruct, edge);
    
    move(translationAmount)
    rot(rotationAmount)
    debug_bezier(bezpath = extractedEdgeCurve);
}

/*
    Extracts the bezier curve that defines the edge of a Bezier patch
    UNFINISHED

    patch : bezier patch
    edge : edge to select, a 2D attachment vector 
*/
function ExtractPatchEdge(patch, edge) =
    let(
        patchDimensions = list_shape(patch),
        
        edgeRowColumnLookupStruct = struct_set([],
                        [BACK, [0, undef],
                        FRONT, [patchDimensions[0]-1, undef],
                        LEFT, [undef, 0],
                        RIGHT, [undef, patchDimensions[1]-1]
                        ]),
        rowColumnIndex = struct_val(edgeRowColumnLookupStruct, edge),
        
        edgeToRelevantCoordinateIndiciesLookupStruct = struct_set([],
                        [BACK, [1, 0, 1],
                        FRONT, [1, 0, 1],
                        LEFT, [0, 1, 1],
                        RIGHT, [0, 1, 1]
                        ]),
        relevantCoordinateIndicies = struct_val(edgeToRelevantCoordinateIndiciesLookupStruct, edge),

        rowIndex = rowColumnIndex[0],
        columnIndex = rowColumnIndex[1],

        patchEdge3DBezPoints = is_def(rowIndex)
            ? ExtractRow(patch, rowIndex)
            : ExtractColumn(patch, columnIndex),

        patchEdgeBezPoints = ExtractElementIndicies(patchEdge3DBezPoints, relevantCoordinateIndicies)
    ) patchEdgeBezPoints;
//