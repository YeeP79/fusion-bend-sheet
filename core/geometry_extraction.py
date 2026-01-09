"""Geometry extraction utilities for sketch entities.

This module provides functions to extract geometric properties from
Fusion 360 sketch entities (lines and arcs).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..models.types import Point3D, ElementType
from .geometry import points_are_close

if TYPE_CHECKING:
    pass

# Type alias for sketch entities we work with
SketchEntity = 'adsk.fusion.SketchLine | adsk.fusion.SketchArc'


def get_sketch_entity_endpoints(entity: SketchEntity) -> tuple[Point3D, Point3D]:
    """
    Extract world-space endpoints from a sketch entity.

    Args:
        entity: A SketchLine or SketchArc

    Returns:
        Tuple of (start_point, end_point) in world coordinates (cm)
    """
    start = entity.startSketchPoint.worldGeometry
    end = entity.endSketchPoint.worldGeometry
    return (
        (start.x, start.y, start.z),
        (end.x, end.y, end.z)
    )


def get_component_name(entity: SketchEntity) -> str:
    """
    Extract the parent component name from a sketch entity.

    Args:
        entity: A sketch entity

    Returns:
        Component name or empty string if not found
    """
    try:
        parent_sketch = entity.parentSketch
        if parent_sketch and parent_sketch.parentComponent:
            return parent_sketch.parentComponent.name
    except Exception:
        pass
    return ""


@dataclass(slots=True)
class PathElement:
    """Wrapper for a path element (line or arc) with metadata."""

    element_type: ElementType
    entity: SketchEntity
    endpoints: tuple[Point3D, Point3D] = field(init=False)

    def __post_init__(self) -> None:
        self.endpoints = get_sketch_entity_endpoints(self.entity)


def get_free_endpoint(element: PathElement, all_elements: list[PathElement]) -> Point3D:
    """Get the endpoint of an element that doesn't connect to any other element."""
    for ep in element.endpoints:
        connected = False
        for other in all_elements:
            if other is element:
                continue
            if points_are_close(ep, other.endpoints[0]) or points_are_close(ep, other.endpoints[1]):
                connected = True
                break
        if not connected:
            return ep
    return element.endpoints[0]


def determine_primary_axis(start: Point3D, end: Point3D) -> tuple[str, int, str, str]:
    """
    Determine the primary travel axis and direction.

    Args:
        start: Start point of path
        end: End point of path

    Returns:
        Tuple of (axis_name, axis_index, current_direction, opposite_direction)
    """
    displacement = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    abs_disp = (abs(displacement[0]), abs(displacement[1]), abs(displacement[2]))
    max_disp = max(abs_disp)

    if abs_disp[0] == max_disp:
        axis, idx = 'X', 0
    elif abs_disp[1] == max_disp:
        axis, idx = 'Y', 1
    else:
        axis, idx = 'Z', 2

    current = f"+{axis}" if displacement[idx] > 0 else f"-{axis}"
    opposite = f"-{axis}" if displacement[idx] > 0 else f"+{axis}"

    return axis, idx, current, opposite
