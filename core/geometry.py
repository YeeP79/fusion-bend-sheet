"""3D vector math and geometry utilities."""

from __future__ import annotations

import math

from ..models.types import Vector3D, Point3D
from .tolerances import CONNECTIVITY_CM, ZERO_MAGNITUDE, COLLINEAR_ANGLE_DEG



class ZeroVectorError(ValueError):
    """Raised when a zero-length vector is used in calculations requiring non-zero vectors."""

    pass


def cross_product(v1: Vector3D, v2: Vector3D) -> Vector3D:
    """
    Calculate the cross product of two 3D vectors.
    
    Args:
        v1: First vector (x, y, z)
        v2: Second vector (x, y, z)
        
    Returns:
        Cross product vector (x, y, z)
    """
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0]
    )


def dot_product(v1: Vector3D, v2: Vector3D) -> float:
    """
    Calculate the dot product of two 3D vectors.
    
    Args:
        v1: First vector (x, y, z)
        v2: Second vector (x, y, z)
        
    Returns:
        Scalar dot product
    """
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]


def magnitude(v: Vector3D) -> float:
    """
    Calculate the magnitude (length) of a 3D vector.

    Args:
        v: Vector (x, y, z)

    Returns:
        Scalar magnitude
    """
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)


def _safe_magnitude_product(v1: Vector3D, v2: Vector3D) -> float:
    """
    Calculate the product of magnitudes, raising if either vector has zero length.

    Args:
        v1: First vector
        v2: Second vector

    Returns:
        Product of magnitudes (mag1 * mag2)

    Raises:
        ZeroVectorError: If either vector has zero or near-zero length
    """
    mag1 = magnitude(v1)
    mag2 = magnitude(v2)

    if mag1 < ZERO_MAGNITUDE:
        raise ZeroVectorError(
            f"First vector has zero length (magnitude={mag1}): {v1}"
        )
    if mag2 < ZERO_MAGNITUDE:
        raise ZeroVectorError(
            f"Second vector has zero length (magnitude={mag2}): {v2}"
        )

    return mag1 * mag2


def angle_between_vectors(v1: Vector3D, v2: Vector3D) -> float:
    """
    Calculate the angle between two vectors in degrees.

    Args:
        v1: First vector
        v2: Second vector

    Returns:
        Angle in degrees (0-180)

    Raises:
        ZeroVectorError: If either vector has zero length
    """
    mag_product = _safe_magnitude_product(v1, v2)
    cos_angle: float = dot_product(v1, v2) / mag_product
    cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp for floating point errors
    return math.degrees(math.acos(cos_angle))


def calculate_rotation(n1: Vector3D, n2: Vector3D) -> float:
    """
    Calculate the rotation angle between two bend plane normals.

    This is the angle you rotate the tube between bends on the bender.

    Args:
        n1: Normal vector of first bend plane
        n2: Normal vector of second bend plane

    Returns:
        Rotation angle in degrees (0-180)

    Raises:
        ZeroVectorError: If either normal vector has zero length
    """
    mag_product = _safe_magnitude_product(n1, n2)
    cos_theta: float = dot_product(n1, n2) / mag_product
    cos_theta = max(-1.0, min(1.0, cos_theta))  # Clamp for floating point errors
    return math.degrees(math.acos(cos_theta))


def distance_between_points(p1: Point3D, p2: Point3D) -> float:
    """
    Calculate the Euclidean distance between two 3D points.
    
    Args:
        p1: First point (x, y, z)
        p2: Second point (x, y, z)
        
    Returns:
        Distance between points
    """
    return math.sqrt(
        (p2[0] - p1[0])**2 +
        (p2[1] - p1[1])**2 +
        (p2[2] - p1[2])**2
    )


def points_are_close(p1: Point3D, p2: Point3D,
                     tolerance: float = CONNECTIVITY_CM) -> bool:
    """
    Check if two points are within tolerance of each other.

    Args:
        p1: First point
        p2: Second point
        tolerance: Maximum distance to consider "close"

    Returns:
        True if points are within or equal to tolerance distance
    """
    return distance_between_points(p1, p2) <= tolerance


def normalize(v: Vector3D) -> Vector3D:
    """
    Normalize a vector to unit length.

    Args:
        v: Vector (x, y, z)

    Returns:
        Unit vector in the same direction

    Raises:
        ZeroVectorError: If vector has zero or near-zero length
    """
    mag = magnitude(v)
    if mag < ZERO_MAGNITUDE:
        raise ZeroVectorError(f"Cannot normalize zero-length vector: {v}")
    return (v[0] / mag, v[1] / mag, v[2] / mag)


def project_onto_plane(v: Vector3D, plane_normal: Vector3D) -> Vector3D:
    """
    Project vector v onto the plane defined by plane_normal.

    Removes the component of v that is parallel to plane_normal.

    Args:
        v: Vector to project
        plane_normal: Normal vector of the plane (does not need to be unit length)

    Returns:
        The component of v lying in the plane

    Raises:
        ZeroVectorError: If plane_normal has zero length
    """
    n = normalize(plane_normal)
    d = dot_product(v, n)
    return (v[0] - d * n[0], v[1] - d * n[1], v[2] - d * n[2])


def subtract_vectors(v1: Vector3D, v2: Vector3D) -> Vector3D:
    """Subtract v2 from v1 component-wise.

    Args:
        v1: First vector.
        v2: Second vector.

    Returns:
        (v1 - v2) as a Vector3D.
    """
    return (v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2])


def add_vectors(v1: Vector3D, v2: Vector3D) -> Vector3D:
    """Add two vectors component-wise.

    Args:
        v1: First vector.
        v2: Second vector.

    Returns:
        (v1 + v2) as a Vector3D.
    """
    return (v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2])


def scale_vector(v: Vector3D, scalar: float) -> Vector3D:
    """Scale a vector by a scalar factor.

    Args:
        v: Vector to scale.
        scalar: Scale factor.

    Returns:
        Scaled vector.
    """
    return (v[0] * scalar, v[1] * scalar, v[2] * scalar)


def point_to_line_distance(
    point: Point3D,
    line_origin: Point3D,
    line_direction: Vector3D,
) -> float:
    """Distance from a point to an infinite line.

    Args:
        point: The query point.
        line_origin: A point on the line.
        line_direction: Normalized direction of the line.

    Returns:
        Perpendicular distance from the point to the line.
    """
    v = subtract_vectors(point, line_origin)
    proj = dot_product(v, line_direction)
    closest = add_vectors(line_origin, scale_vector(line_direction, proj))
    return distance_between_points(point, closest)


def unsigned_angle_between(v1: Vector3D, v2: Vector3D) -> float:
    """Angle between two vectors, treating parallel and anti-parallel the same.

    Returns an angle in degrees in the range [0, 90].

    Args:
        v1: First vector.
        v2: Second vector.

    Returns:
        Unsigned angle in degrees (0-90).

    Raises:
        ZeroVectorError: If either vector has zero length.
    """
    mag_product = _safe_magnitude_product(v1, v2)
    cos_angle: float = dot_product(v1, v2) / mag_product
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(abs(cos_angle)))


def bbox_axial_extent(
    bbox_min: Point3D,
    bbox_max: Point3D,
    axis_origin: Point3D,
    axis_dir: Vector3D,
) -> tuple[float, float]:
    """Project all 8 bounding box corners onto an axis and return the extent.

    This correctly handles non-axis-aligned tubes by testing all 8 corner
    combinations.  Using only (minPoint, maxPoint) — i.e. 2 of 8 corners —
    gives wrong results when the axis direction has mixed-sign components.

    Args:
        bbox_min: Bounding box minimum corner (x, y, z).
        bbox_max: Bounding box maximum corner (x, y, z).
        axis_origin: A point on the projection axis.
        axis_dir: Direction of the projection axis (need not be normalized).

    Returns:
        (min_projection, max_projection) along the axis.
    """
    t_min = float("inf")
    t_max = float("-inf")

    for x in (bbox_min[0], bbox_max[0]):
        for y in (bbox_min[1], bbox_max[1]):
            for z in (bbox_min[2], bbox_max[2]):
                dx = x - axis_origin[0]
                dy = y - axis_origin[1]
                dz = z - axis_origin[2]
                t = dx * axis_dir[0] + dy * axis_dir[1] + dz * axis_dir[2]
                t_min = min(t_min, t)
                t_max = max(t_max, t)

    return t_min, t_max


def vectors_are_collinear(
    v1: Vector3D,
    v2: Vector3D,
    tolerance_deg: float = COLLINEAR_ANGLE_DEG,
) -> bool:
    """
    Check if two vectors are collinear (parallel or anti-parallel).

    Args:
        v1: First vector
        v2: Second vector
        tolerance_deg: Maximum angle deviation in degrees (floating point tolerance)

    Returns:
        True if vectors are within tolerance of being parallel or anti-parallel.
        Returns False if either vector has zero length.
    """
    try:
        angle = angle_between_vectors(v1, v2)
    except ZeroVectorError:
        return False
    return angle < tolerance_deg or angle > 180.0 - tolerance_deg
