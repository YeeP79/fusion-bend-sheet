"""Path analysis for tube bend geometry.

DEPRECATED: This module re-exports from geometry_extraction and path_ordering
for backward compatibility. New code should import directly from those modules.
"""

from .geometry_extraction import (
    SketchEntity,
    get_sketch_entity_endpoints,
    get_component_name,
    PathElement,
    get_free_endpoint,
    determine_primary_axis,
)
from .path_ordering import (
    elements_are_connected,
    build_ordered_path,
    validate_path_alternation,
)

__all__ = [
    # Geometry extraction
    'SketchEntity',
    'get_sketch_entity_endpoints',
    'get_component_name',
    'PathElement',
    'get_free_endpoint',
    'determine_primary_axis',
    # Path ordering
    'elements_are_connected',
    'build_ordered_path',
    'validate_path_alternation',
]
