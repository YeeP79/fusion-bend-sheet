"""
Tests for geometry module - runs without Fusion.

Run with: pytest tests/ -v
"""
import math

from core.geometry import (
    ZeroVectorError,
    angle_between_vectors,
    calculate_rotation,
    cross_product,
    distance_between_points,
    dot_product,
    magnitude,
    points_are_close,
)


class TestVectorOperations:
    """Test basic vector operations."""

    def test_magnitude_unit_vector(self):
        assert magnitude((1.0, 0.0, 0.0)) == 1.0

    def test_magnitude_3_4_5_triangle(self):
        assert magnitude((3.0, 4.0, 0.0)) == 5.0

    def test_magnitude_zero_vector(self):
        assert magnitude((0.0, 0.0, 0.0)) == 0.0

    def test_magnitude_negative_components(self):
        assert magnitude((-3.0, -4.0, 0.0)) == 5.0

    def test_dot_product_perpendicular(self):
        result = dot_product((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        assert result == 0.0

    def test_dot_product_parallel(self):
        result = dot_product((1.0, 0.0, 0.0), (2.0, 0.0, 0.0))
        assert result == 2.0

    def test_cross_product_unit_vectors(self):
        result = cross_product((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        assert result == (0.0, 0.0, 1.0)

    def test_cross_product_antiparallel(self):
        result = cross_product((0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
        assert result == (0.0, 0.0, -1.0)


class TestAngleBetweenVectors:
    """Test angle calculations with defensive cases."""

    def test_parallel_vectors_zero_degrees(self):
        angle = angle_between_vectors((1.0, 0.0, 0.0), (2.0, 0.0, 0.0))
        assert abs(angle) < 0.001

    def test_antiparallel_vectors_180_degrees(self):
        angle = angle_between_vectors((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0))
        assert abs(angle - 180.0) < 0.001

    def test_perpendicular_vectors_90_degrees(self):
        angle = angle_between_vectors((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        assert abs(angle - 90.0) < 0.001

    def test_45_degree_angle(self):
        angle = angle_between_vectors((1.0, 0.0, 0.0), (1.0, 1.0, 0.0))
        assert abs(angle - 45.0) < 0.001

    def test_zero_first_vector_raises(self):
        try:
            angle_between_vectors((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
            raise AssertionError("Should have raised ZeroVectorError")
        except ZeroVectorError as e:
            assert "First vector" in str(e)

    def test_zero_second_vector_raises(self):
        try:
            angle_between_vectors((1.0, 0.0, 0.0), (0.0, 0.0, 0.0))
            raise AssertionError("Should have raised ZeroVectorError")
        except ZeroVectorError as e:
            assert "Second vector" in str(e)

    def test_near_zero_vector_raises(self):
        """Vectors below tolerance should raise."""
        try:
            angle_between_vectors((1e-11, 0.0, 0.0), (1.0, 0.0, 0.0))
            raise AssertionError("Should have raised ZeroVectorError")
        except ZeroVectorError:
            pass

    def test_no_nan_from_nearly_parallel(self):
        """Ensure floating point edge case doesn't produce NaN."""
        angle = angle_between_vectors((1.0, 0.0, 0.0), (0.9999999, 0.0001, 0.0))
        assert not math.isnan(angle)
        assert 0 <= angle <= 180


class TestCalculateRotation:
    """Test rotation angle calculations."""

    def test_same_plane_zero_rotation(self):
        rotation = calculate_rotation((0.0, 0.0, 1.0), (0.0, 0.0, 1.0))
        assert abs(rotation) < 0.001

    def test_90_degree_rotation(self):
        rotation = calculate_rotation((0.0, 0.0, 1.0), (0.0, 1.0, 0.0))
        assert abs(rotation - 90.0) < 0.001

    def test_180_degree_rotation(self):
        rotation = calculate_rotation((0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
        assert abs(rotation - 180.0) < 0.001

    def test_zero_normal_raises(self):
        try:
            calculate_rotation((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
            raise AssertionError("Should have raised ZeroVectorError")
        except ZeroVectorError:
            pass


class TestPointOperations:
    """Test point-related functions."""

    def test_distance_same_point(self):
        dist = distance_between_points((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        assert dist == 0.0

    def test_distance_unit_apart(self):
        dist = distance_between_points((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
        assert dist == 1.0

    def test_distance_3d(self):
        dist = distance_between_points((0.0, 0.0, 0.0), (1.0, 2.0, 2.0))
        assert dist == 3.0

    def test_points_are_close_same(self):
        assert points_are_close((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))

    def test_points_are_close_within_tolerance(self):
        assert points_are_close((0.0, 0.0, 0.0), (0.05, 0.0, 0.0), tolerance=0.1)

    def test_points_are_close_outside_tolerance(self):
        assert not points_are_close((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), tolerance=0.1)
