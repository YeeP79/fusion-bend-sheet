"""Bend calculation logic."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ..models.types import Vector3D, Point3D
from .geometry import (
    cross_product,
    magnitude,
    angle_between_vectors,
    calculate_rotation,
    distance_between_points,
)
from .path_analysis import get_sketch_entity_endpoints

if TYPE_CHECKING:
    import adsk.fusion

from ..models.bend_data import StraightSection, BendData, PathSegment, MarkPosition
from ..models.units import UnitConfig

# CLR tolerance as a ratio for detecting mismatched bend radii.
# A 0.2% tolerance means two CLR values are considered matching if they differ
# by less than 0.2% of the nominal CLR. For example:
#   - 5.5" CLR with 0.2% tolerance allows ±0.011" variance
#   - 140mm CLR with 0.2% tolerance allows ±0.28mm variance
# This accounts for minor CAD rounding and manufacturing tolerances while
# still detecting when bends use genuinely different dies.
CLR_TOLERANCE_RATIO: float = 0.002


def validate_clr_consistency(
    arcs: list['adsk.fusion.SketchArc'],
    units: UnitConfig
) -> tuple[float, bool, list[float]]:
    """
    Extract and validate CLR from arc geometry.
    
    Args:
        arcs: List of sketch arcs
        units: Unit configuration for conversion
        
    Returns:
        Tuple of (primary_clr, has_mismatch, all_clr_values) in display units
    """
    clr_values: list[float] = []
    for arc in arcs:
        # arc.radius is in cm (Fusion internal)
        clr_display = arc.radius * units.cm_to_unit
        clr_values.append(clr_display)
    
    if not clr_values:
        return 0.0, False, []

    clr = clr_values[0]

    # Check for degenerate arc (zero or negative CLR)
    if clr <= 0:
        return 0.0, True, clr_values

    # Use ratio-based tolerance (0.2% of CLR) with minimum floor
    # The minimum floor prevents false mismatches with very small CLR values
    tolerance = max(clr * CLR_TOLERANCE_RATIO, 0.001)
    has_mismatch = any(abs(c - clr) > tolerance for c in clr_values)
    
    return clr, has_mismatch, clr_values


def calculate_straights_and_bends(
    lines: list['adsk.fusion.SketchLine'],
    arcs: list['adsk.fusion.SketchArc'],
    path_start: Point3D,
    clr: float,
    units: UnitConfig
) -> tuple[list[StraightSection], list[BendData]]:
    """
    Calculate all straight sections and bend data from geometry.
    
    Args:
        lines: Ordered list of sketch lines
        arcs: Ordered list of sketch arcs
        path_start: The starting point of the path (in cm)
        clr: Center line radius in display units
        units: Unit configuration for conversion
        
    Returns:
        Tuple of (straights, bends) with lengths in display units
    """
    # Get line endpoints and orient them correctly
    line_points: list[tuple[Point3D, Point3D]] = []
    for line in lines:
        start, end = get_sketch_entity_endpoints(line)
        line_points.append((start, end))

    # Validate we have geometry to process
    if not line_points:
        raise ValueError("No lines provided - cannot calculate bend data")

    # Orient first line so start is at path_start
    corrected: list[tuple[Point3D, Point3D]] = []
    first_start, first_end = line_points[0]
    
    if distance_between_points(first_end, path_start) < distance_between_points(first_start, path_start):
        corrected.append((first_end, first_start))
    else:
        corrected.append((first_start, first_end))
    
    # Orient remaining lines based on connectivity
    for i in range(1, len(line_points)):
        prev_end = corrected[i - 1][1]
        curr_start, curr_end = line_points[i]
        
        if distance_between_points(curr_end, prev_end) < distance_between_points(curr_start, prev_end):
            corrected.append((curr_end, curr_start))
        else:
            corrected.append((curr_start, curr_end))
    
    # Build straight sections
    straights: list[StraightSection] = []
    vectors: list[Vector3D] = []
    
    for i, (start, end) in enumerate(corrected):
        vector: Vector3D = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
        vectors.append(vector)
        
        length_cm = magnitude(vector)
        length_display = length_cm * units.cm_to_unit
        
        straights.append(StraightSection(
            number=i + 1,
            length=length_display,
            start=(
                start[0] * units.cm_to_unit,
                start[1] * units.cm_to_unit,
                start[2] * units.cm_to_unit
            ),
            end=(
                end[0] * units.cm_to_unit,
                end[1] * units.cm_to_unit,
                end[2] * units.cm_to_unit
            ),
            vector=vector
        ))
    
    # Calculate bend plane normals
    # Each bend requires two adjacent vectors (incoming and outgoing)
    if len(vectors) < len(arcs) + 1:
        raise ValueError(
            f"Insufficient vectors ({len(vectors)}) for {len(arcs)} arcs - "
            "expected at least arcs + 1 vectors"
        )

    normals: list[Vector3D] = []
    for i in range(len(arcs)):
        n = cross_product(vectors[i], vectors[i + 1])
        normals.append(n)
    
    # Calculate bend angles and rotations
    bends: list[BendData] = []
    for i in range(len(arcs)):
        bend_angle = angle_between_vectors(vectors[i], vectors[i + 1])
        arc_length = clr * math.radians(bend_angle)
        
        rotation: float | None = None
        if i > 0:
            rotation = calculate_rotation(normals[i - 1], normals[i])
        
        bends.append(BendData(
            number=i + 1,
            angle=bend_angle,
            rotation=rotation,
            arc_length=arc_length
        ))
    
    return straights, bends


def build_segments_and_marks(
    straights: list[StraightSection],
    bends: list[BendData],
    extra_material: float,
    die_offset: float
) -> tuple[list[PathSegment], list[MarkPosition]]:
    """
    Build cumulative path segments and mark positions.
    
    Args:
        straights: List of straight sections
        bends: List of bend data
        extra_material: Extra grip material at start
        die_offset: Die offset in display units
        
    Returns:
        Tuple of (segments, mark_positions)
    """
    segments: list[PathSegment] = []
    cumulative = extra_material
    
    for i, straight in enumerate(straights):
        # Add straight segment
        segments.append(PathSegment(
            segment_type='straight',
            name=f'Straight {straight.number}',
            length=straight.length,
            starts_at=cumulative,
            ends_at=cumulative + straight.length,
            bend_angle=None,
            rotation=bends[i].rotation if i < len(bends) else None
        ))
        cumulative += straight.length
        
        # Add bend segment (if not last straight)
        if i < len(bends):
            bend = bends[i]
            segments.append(PathSegment(
                segment_type='bend',
                name=f'BEND {bend.number}',
                length=bend.arc_length,
                starts_at=cumulative,
                ends_at=cumulative + bend.arc_length,
                bend_angle=bend.angle,
                rotation=None
            ))
            cumulative += bend.arc_length
    
    # Calculate mark positions
    mark_positions: list[MarkPosition] = []
    for bend in bends:
        # Find where this bend starts
        bend_starts_at = 0.0
        for seg in segments:
            if seg.segment_type == 'bend' and seg.name == f'BEND {bend.number}':
                bend_starts_at = seg.starts_at
                break
        
        mark_positions.append(MarkPosition(
            bend_num=bend.number,
            mark_position=bend_starts_at - die_offset,
            bend_angle=bend.angle,
            rotation=bend.rotation
        ))
    
    return segments, mark_positions
