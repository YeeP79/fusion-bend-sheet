"""Core calculation and geometry utilities."""

from .geometry import (
    cross_product,
    dot_product,
    magnitude,
    angle_between_vectors,
    calculate_rotation,
    distance_between_points,
    points_are_close,
)
from .path_analysis import (
    PathElement,
    get_sketch_entity_endpoints,
    get_component_name,
    build_ordered_path,
    validate_path_alternation,
    get_free_endpoint,
    determine_primary_axis,
)
from .calculations import (
    validate_clr_consistency,
    calculate_straights_and_bends,
    build_segments_and_marks,
)
from .formatting import (
    format_length,
    get_precision_label,
)
from .html_generator import generate_html_bend_sheet

__all__ = [
    # Geometry
    'cross_product',
    'dot_product',
    'magnitude',
    'angle_between_vectors',
    'calculate_rotation',
    'distance_between_points',
    'points_are_close',
    # Path analysis
    'PathElement',
    'get_sketch_entity_endpoints',
    'get_component_name',
    'build_ordered_path',
    'validate_path_alternation',
    'get_free_endpoint',
    'determine_primary_axis',
    # Calculations
    'validate_clr_consistency',
    'calculate_straights_and_bends',
    'build_segments_and_marks',
    # Formatting
    'format_length',
    'get_precision_label',
    # HTML
    'generate_html_bend_sheet',
]
