"""Selection validation for Create Bend Sheet command.

This module validates user selections and extracts geometry data,
following SRP by separating validation from UI and business logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import adsk.core
import adsk.fusion

from ...core import (
    PathElement,
    build_ordered_path,
    validate_path_alternation,
    get_free_endpoint,
    determine_primary_axis,
    get_component_name,
)
from ...models import UnitConfig


@dataclass(slots=True)
class SelectionResult:
    """Result of validating and analyzing user selection.

    Contains all extracted geometry data needed for bend sheet generation.
    """

    is_valid: bool
    error_message: str | None = None

    # Raw geometry
    lines: list[adsk.fusion.SketchLine] = field(default_factory=list)
    arcs: list[adsk.fusion.SketchArc] = field(default_factory=list)

    # Ordered path
    ordered_path: list[PathElement] = field(default_factory=list)

    # Path properties
    first_entity: adsk.fusion.SketchEntity | None = None
    detected_clr: float = 0.0
    component_name: str = ""
    starts_with_arc: bool = False
    ends_with_arc: bool = False

    # Direction info
    start_point: tuple[float, float, float] | None = None
    end_point: tuple[float, float, float] | None = None
    primary_axis: str = ""
    travel_direction: str = ""
    opposite_direction: str = ""


class SelectionValidator:
    """Validate and analyze user selection for bend sheet generation.

    Responsible for:
    - Checking selection count requirements
    - Extracting lines and arcs from selection
    - Building and validating ordered path
    - Extracting geometry properties (CLR, axis, direction)
    """

    MIN_SELECTION_COUNT: int = 3

    def __init__(self, units: UnitConfig) -> None:
        """
        Initialize the validator.

        Args:
            units: Unit configuration for the design
        """
        self._units = units

    def validate_for_dialog(
        self,
        selections: adsk.core.Selections,
    ) -> SelectionResult:
        """
        Perform validation for dialog creation.

        This validates selection count, builds ordered path, and extracts
        geometry info needed for populating the dialog including direction.

        Args:
            selections: Active selections from the UI

        Returns:
            SelectionResult with validation status and geometry data
        """
        # Check minimum selection count
        if selections.count < self.MIN_SELECTION_COUNT:
            return SelectionResult(
                is_valid=False,
                error_message=(
                    "Please select the tube path elements first:\n\n"
                    "Select all straight sections (lines) AND bends (arcs).\n"
                    "You can select them in any order."
                ),
            )

        # Extract geometry
        lines, arcs, first_entity = self._extract_geometry(selections)

        # Detect CLR from first arc
        detected_clr: float = 0.0
        if arcs:
            detected_clr = arcs[0].radius * self._units.cm_to_unit

        # Build path elements
        elements: list[PathElement] = []
        for line in lines:
            elements.append(PathElement("line", line))
        for arc in arcs:
            elements.append(PathElement("arc", arc))

        # Build ordered path
        ordered, path_error = build_ordered_path(elements)
        if ordered is None:
            return SelectionResult(
                is_valid=False,
                error_message=f"Path ordering error: {path_error}",
                lines=lines,
                arcs=arcs,
                first_entity=first_entity,
                detected_clr=detected_clr,
            )

        # Validate path alternation
        is_valid_path, error_msg = validate_path_alternation(ordered)
        if not is_valid_path:
            return SelectionResult(
                is_valid=False,
                error_message=f"Path structure error: {error_msg}",
                lines=lines,
                arcs=arcs,
                first_entity=first_entity,
                detected_clr=detected_clr,
            )

        # Extract path properties
        starts_with_arc = ordered[0].element_type == "arc"
        ends_with_arc = ordered[-1].element_type == "arc"
        component_name = get_component_name(ordered[0].entity)

        # Get start/end points
        start_point = get_free_endpoint(ordered[0], ordered)
        end_point = get_free_endpoint(ordered[-1], ordered)

        # Determine primary axis and directions
        axis, _, current_dir, opposite_dir = determine_primary_axis(
            start_point, end_point
        )

        return SelectionResult(
            is_valid=True,
            lines=lines,
            arcs=arcs,
            ordered_path=ordered,
            first_entity=first_entity,
            detected_clr=detected_clr,
            component_name=component_name,
            starts_with_arc=starts_with_arc,
            ends_with_arc=ends_with_arc,
            start_point=start_point,
            end_point=end_point,
            primary_axis=axis,
            travel_direction=current_dir,
            opposite_direction=opposite_dir,
        )

    def validate_for_execution(
        self,
        selections: adsk.core.Selections,
    ) -> SelectionResult:
        """
        Perform full validation for command execution.

        This is now equivalent to validate_for_dialog() since that method
        was enhanced to include all necessary validation and geometry extraction.

        Args:
            selections: Active selections from the UI

        Returns:
            SelectionResult with full validation and geometry data
        """
        # All validation is now done in validate_for_dialog()
        return self.validate_for_dialog(selections)

    def _extract_geometry(
        self,
        selections: adsk.core.Selections,
    ) -> tuple[
        list[adsk.fusion.SketchLine],
        list[adsk.fusion.SketchArc],
        adsk.fusion.SketchEntity | None,
    ]:
        """
        Extract lines and arcs from selection.

        Args:
            selections: Active selections from the UI

        Returns:
            Tuple of (lines, arcs, first_entity)
        """
        lines: list[adsk.fusion.SketchLine] = []
        arcs: list[adsk.fusion.SketchArc] = []
        first_entity: adsk.fusion.SketchEntity | None = None

        for i in range(selections.count):
            entity = selections.item(i).entity
            if first_entity is None:
                first_entity = entity

            line = adsk.fusion.SketchLine.cast(entity)
            if line:
                lines.append(line)
                continue

            arc = adsk.fusion.SketchArc.cast(entity)
            if arc:
                arcs.append(arc)

        return lines, arcs, first_entity
