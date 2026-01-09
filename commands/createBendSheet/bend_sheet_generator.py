"""Orchestrates bend sheet calculation and data building.

This module coordinates the calculation pipeline to generate complete
bend sheet data from geometry and parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...core import (
    validate_clr_consistency,
    calculate_straights_and_bends,
    build_segments_and_marks,
)
from ...models import UnitConfig, BendSheetData

if TYPE_CHECKING:
    import adsk.fusion

    from ...core import PathElement
    from .input_parser import BendSheetParams


@dataclass(slots=True)
class GenerationResult:
    """Result of bend sheet generation."""

    success: bool
    data: BendSheetData | None = None
    error: str = ""


class BendSheetGenerator:
    """Generates bend sheet data from geometry and parameters.

    Responsible for:
    - Validating CLR consistency
    - Calculating straights and bends
    - Building segments and mark positions
    - Constructing complete BendSheetData
    """

    def __init__(self, units: UnitConfig) -> None:
        """
        Initialize the generator.

        Args:
            units: Unit configuration for the design
        """
        self._units = units

    def generate(
        self,
        ordered_path: list["PathElement"],
        start_point: tuple[float, float, float],
        params: "BendSheetParams",
        component_name: str,
        travel_direction: str,
        starts_with_arc: bool,
        ends_with_arc: bool,
    ) -> GenerationResult:
        """
        Generate complete bend sheet data.

        Args:
            ordered_path: Ordered list of path elements (lines and arcs)
            start_point: Starting point of the path
            params: Parsed input parameters
            component_name: Name of the component
            travel_direction: Direction of travel along path
            starts_with_arc: Whether path starts with an arc
            ends_with_arc: Whether path ends with an arc

        Returns:
            GenerationResult with success status and data or error
        """
        # Extract lines and arcs from ordered path
        lines: list[adsk.fusion.SketchLine] = [
            e.entity for e in ordered_path if e.element_type == "line"
        ]
        arcs: list[adsk.fusion.SketchArc] = [
            e.entity for e in ordered_path if e.element_type == "arc"
        ]

        # Validate CLR consistency
        clr, clr_mismatch, clr_values = validate_clr_consistency(arcs, self._units)

        # Calculate straights and bends
        straights, bends = calculate_straights_and_bends(
            lines, arcs, start_point, clr, self._units
        )

        # Validate we have straight sections
        if not straights:
            return GenerationResult(
                success=False,
                error="No straight sections found in path. Cannot generate bend sheet.",
            )

        # Calculate extra material needed for grip
        first_feed: float = straights[0].length - params.die_offset
        extra_material: float = (
            max(0.0, params.min_grip - first_feed) if params.min_grip > 0 else 0.0
        )

        # Validate straight sections against min_grip
        # Check first straight and all straights between bends (not the last one)
        grip_violations: list[int] = []
        if params.min_grip > 0 and len(straights) > 1:
            sections_to_check = straights[:-1]  # All except the last one
            for straight in sections_to_check:
                if straight.length < params.min_grip:
                    grip_violations.append(straight.number)

        # Validate last straight section against min_tail
        tail_violation: bool = False
        if params.min_tail > 0 and len(straights) > 0:
            last_straight = straights[-1]
            if last_straight.length < params.min_tail:
                tail_violation = True

        # Build segments and mark positions
        segments, mark_positions = build_segments_and_marks(
            straights, bends, extra_material, params.die_offset
        )

        # Calculate totals
        total_straights: float = sum(s.length for s in straights)
        total_arcs: float = sum(b.arc_length for b in bends)
        total_centerline: float = total_straights + total_arcs
        total_cut_length: float = total_centerline + extra_material

        # Build sheet data
        sheet_data = BendSheetData(
            component_name=component_name,
            tube_od=params.tube_od,
            clr=clr,
            die_offset=params.die_offset,
            precision=params.precision,
            min_grip=params.min_grip,
            travel_direction=travel_direction,
            starts_with_arc=starts_with_arc,
            ends_with_arc=ends_with_arc,
            clr_mismatch=clr_mismatch,
            clr_values=clr_values,
            continuity_errors=[],
            straights=straights,
            bends=bends,
            segments=segments,
            mark_positions=mark_positions,
            extra_material=extra_material,
            total_centerline=total_centerline,
            total_cut_length=total_cut_length,
            units=self._units,
            bender_name=params.bender_name,
            die_name=params.die_name,
            grip_violations=grip_violations,
            min_tail=params.min_tail,
            tail_violation=tail_violation,
        )

        return GenerationResult(success=True, data=sheet_data)
