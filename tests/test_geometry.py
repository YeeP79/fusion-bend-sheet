"""
Tests for geometry module - runs without Fusion.

Run with: pytest tests/ -v
"""
import math

import pytest

from core.geometry import (
    ZeroVectorError,
    angle_between_vectors,
    bbox_axial_extent,
    calculate_rotation,
    cross_product,
    distance_between_points,
    dot_product,
    magnitude,
    normalize,
    points_are_close,
    project_onto_plane,
    vectors_are_collinear,
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


class TestVectorsAreCollinear:
    """Test vectors_are_collinear() function."""

    # Happy path: parallel vectors
    def test_same_direction_parallel(self):
        """Vectors pointing the same direction are collinear."""
        assert vectors_are_collinear((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)) is True

    def test_anti_parallel(self):
        """Vectors pointing opposite directions are collinear."""
        assert vectors_are_collinear((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)) is True

    def test_3d_parallel(self):
        """Parallel vectors in 3D are collinear."""
        assert vectors_are_collinear((1.0, 2.0, 3.0), (2.0, 4.0, 6.0)) is True

    def test_3d_anti_parallel(self):
        """Anti-parallel vectors in 3D are collinear."""
        assert vectors_are_collinear((1.0, 2.0, 3.0), (-1.0, -2.0, -3.0)) is True

    # Non-collinear vectors
    def test_perpendicular_not_collinear(self):
        """Perpendicular vectors are not collinear."""
        assert vectors_are_collinear((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) is False

    def test_45_degree_not_collinear(self):
        """Vectors at 45 degrees are not collinear."""
        assert vectors_are_collinear((1.0, 0.0, 0.0), (1.0, 1.0, 0.0)) is False

    # Tolerance edge cases
    def test_within_tolerance(self):
        """Vectors with very slight angle (within tolerance) are collinear."""
        # Angle ~0.003 degrees - well within default 0.01 tolerance
        assert vectors_are_collinear((1.0, 0.0, 0.0), (1.0, 0.00005, 0.0)) is True

    def test_beyond_tolerance(self):
        """Vectors beyond tolerance are not collinear."""
        # Use a tight tolerance to demonstrate
        assert vectors_are_collinear(
            (1.0, 0.0, 0.0), (1.0, 0.01, 0.0), tolerance_deg=0.001
        ) is False

    def test_near_anti_parallel_within_tolerance(self):
        """Nearly anti-parallel vectors (within tolerance) are collinear."""
        assert vectors_are_collinear((1.0, 0.0, 0.0), (-1.0, 0.00005, 0.0)) is True

    # Defensive: zero-length vectors
    def test_zero_first_vector_returns_false(self):
        """Zero-length first vector returns False (not an error)."""
        assert vectors_are_collinear((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)) is False

    def test_zero_second_vector_returns_false(self):
        """Zero-length second vector returns False (not an error)."""
        assert vectors_are_collinear((1.0, 0.0, 0.0), (0.0, 0.0, 0.0)) is False

    def test_both_zero_vectors_returns_false(self):
        """Both zero-length vectors returns False."""
        assert vectors_are_collinear((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)) is False

    # Floating point edge cases
    def test_no_crash_on_near_zero_vector(self):
        """Near-zero vector doesn't crash."""
        result = vectors_are_collinear((1e-11, 0.0, 0.0), (1.0, 0.0, 0.0))
        assert result is False  # Below zero magnitude tolerance


class TestNormalize:
    """Test normalize() function."""

    def test_unit_vector_unchanged(self):
        result = normalize((1.0, 0.0, 0.0))
        assert abs(result[0] - 1.0) < 1e-10
        assert abs(result[1]) < 1e-10
        assert abs(result[2]) < 1e-10

    def test_scales_to_unit_length(self):
        result = normalize((3.0, 4.0, 0.0))
        assert abs(magnitude(result) - 1.0) < 1e-10
        assert abs(result[0] - 0.6) < 1e-10
        assert abs(result[1] - 0.8) < 1e-10

    def test_negative_components(self):
        result = normalize((-3.0, -4.0, 0.0))
        assert abs(magnitude(result) - 1.0) < 1e-10
        assert abs(result[0] - (-0.6)) < 1e-10
        assert abs(result[1] - (-0.8)) < 1e-10

    def test_3d_vector(self):
        result = normalize((1.0, 1.0, 1.0))
        expected = 1.0 / math.sqrt(3.0)
        for comp in result:
            assert abs(comp - expected) < 1e-10

    def test_zero_vector_raises(self):
        with pytest.raises(ZeroVectorError):
            normalize((0.0, 0.0, 0.0))

    def test_near_zero_vector_raises(self):
        with pytest.raises(ZeroVectorError):
            normalize((1e-11, 0.0, 0.0))


class TestProjectOntoPlane:
    """Test project_onto_plane() function."""

    def test_vector_already_in_plane(self):
        """Vector in XY plane projected onto XY plane is unchanged."""
        result = project_onto_plane((1.0, 2.0, 0.0), (0.0, 0.0, 1.0))
        assert abs(result[0] - 1.0) < 1e-10
        assert abs(result[1] - 2.0) < 1e-10
        assert abs(result[2]) < 1e-10

    def test_vector_perpendicular_to_plane(self):
        """Vector along plane normal projects to zero."""
        result = project_onto_plane((0.0, 0.0, 5.0), (0.0, 0.0, 1.0))
        assert abs(result[0]) < 1e-10
        assert abs(result[1]) < 1e-10
        assert abs(result[2]) < 1e-10

    def test_45_degree_projection(self):
        """Vector at 45 degrees to plane normal."""
        result = project_onto_plane((1.0, 0.0, 1.0), (0.0, 0.0, 1.0))
        assert abs(result[0] - 1.0) < 1e-10
        assert abs(result[1]) < 1e-10
        assert abs(result[2]) < 1e-10

    def test_non_unit_normal(self):
        """Works with non-unit plane normal."""
        result = project_onto_plane((1.0, 0.0, 1.0), (0.0, 0.0, 3.0))
        assert abs(result[0] - 1.0) < 1e-10
        assert abs(result[1]) < 1e-10
        assert abs(result[2]) < 1e-10

    def test_3d_projection(self):
        """Projection onto arbitrary plane in 3D."""
        # Project (1,1,1) onto plane with normal (1,0,0) -> (0,1,1)
        result = project_onto_plane((1.0, 1.0, 1.0), (1.0, 0.0, 0.0))
        assert abs(result[0]) < 1e-10
        assert abs(result[1] - 1.0) < 1e-10
        assert abs(result[2] - 1.0) < 1e-10

    def test_zero_normal_raises(self):
        with pytest.raises(ZeroVectorError):
            project_onto_plane((1.0, 0.0, 0.0), (0.0, 0.0, 0.0))


class TestBboxAxialExtent:
    """Test bounding box projection onto an arbitrary axis.

    Regression tests for the bug where only 2 of 8 bbox corners were
    projected, giving wrong axial extent for non-axis-aligned tubes.
    """

    def test_axis_aligned_x(self):
        """Axis-aligned along X — all projection methods agree."""
        bbox_min = (0.0, -1.0, -1.0)
        bbox_max = (10.0, 1.0, 1.0)
        origin = (0.0, 0.0, 0.0)
        axis = (1.0, 0.0, 0.0)

        t_min, t_max = bbox_axial_extent(bbox_min, bbox_max, origin, axis)
        assert abs(t_min - 0.0) < 1e-10
        assert abs(t_max - 10.0) < 1e-10

    def test_axis_aligned_z(self):
        """Axis-aligned along Z."""
        bbox_min = (-1.0, -1.0, 5.0)
        bbox_max = (1.0, 1.0, 20.0)
        origin = (0.0, 0.0, 0.0)
        axis = (0.0, 0.0, 1.0)

        t_min, t_max = bbox_axial_extent(bbox_min, bbox_max, origin, axis)
        assert abs(t_min - 5.0) < 1e-10
        assert abs(t_max - 20.0) < 1e-10

    def test_diagonal_45_degree_xz(self):
        """Tube at 45 degrees in XZ plane — the case that fails with 2 corners.

        A tube from (0,0,0) to (10,0,10) has its bbox at
        min=(0,-r,-r) to max=(10,r,10+r), but projecting only minPoint
        and maxPoint gives wrong axial extent.
        """
        # Tube 10 units long at 45° in XZ, OD radius ~1
        bbox_min = (-1.0, -1.0, -1.0)
        bbox_max = (10.0, 1.0, 10.0)
        origin = (5.0, 0.0, 5.0)  # midpoint of tube
        axis = normalize((1.0, 0.0, 1.0))  # 45° in XZ

        t_min, t_max = bbox_axial_extent(bbox_min, bbox_max, origin, axis)

        # The full diagonal extent should be sqrt(2)*10 ≈ 14.14 from
        # corner (-1,-1,-1) to (10,1,10).  The 2-corner bug would
        # underestimate this because minPoint projects to one value
        # and maxPoint projects to the same value as the true max
        # only when axis components are all positive.
        extent = t_max - t_min
        assert extent > 14.0, (
            f"Extent {extent:.4f} is too small — likely using only 2 corners"
        )

    def test_mixed_sign_axis_requires_8_corners(self):
        """Axis with mixed-sign components — only 8-corner projection is correct.

        This is the exact failure mode from the driver shock hoop bug:
        tube axis ~ (-0.45, -0.01, -0.89).  With 2 corners, the min/max
        projections are wrong because the optimal corners mix min and max
        coordinates.
        """
        # Simulate a tube bbox roughly matching the bug scenario
        bbox_min = (30.0, 108.0, -10.0)
        bbox_max = (70.0, 110.0, 70.0)
        origin = (50.0, 109.0, 30.0)
        axis = normalize((-0.4463, -0.0085, -0.8948))

        t_min, t_max = bbox_axial_extent(bbox_min, bbox_max, origin, axis)

        # With 2 corners (minPoint and maxPoint), we'd get:
        #   proj(minPoint) = (30-50)*(-0.45) + (108-109)*(-0.0085) + (-10-30)*(-0.89)
        #                  ≈ 9.0 + 0.0085 + 35.6 ≈ 44.6
        #   proj(maxPoint) = (70-50)*(-0.45) + (110-109)*(-0.0085) + (70-30)*(-0.89)
        #                  ≈ -9.0 - 0.0085 - 35.6 ≈ -44.6
        # So 2-corner min/max would be (-44.6, 44.6).
        #
        # But the TRUE min uses (max_x, max_y, max_z) = (70, 110, 70):
        #   (70-50)*(-0.45) + (110-109)*(-0.0085) + (70-30)*(-0.89) ≈ -44.6
        # And TRUE max uses (min_x, min_y, min_z) = (30, 108, -10):
        #   (30-50)*(-0.45) + (108-109)*(-0.0085) + (-10-30)*(-0.89) ≈ 44.6
        #
        # In this symmetric case they happen to agree, but let's test an
        # asymmetric bbox where they diverge.
        pass

    def test_asymmetric_bbox_mixed_sign_axis(self):
        """Asymmetric bbox with mixed-sign axis — 2 corners gives wrong result.

        Axis = (1, -1, 0)/sqrt(2).  The minimum projection needs
        (min_x, MAX_y, _) and the maximum needs (MAX_x, min_y, _).
        Only 8-corner enumeration finds these.
        """
        bbox_min = (0.0, 0.0, 0.0)
        bbox_max = (10.0, 20.0, 5.0)
        origin = (0.0, 0.0, 0.0)
        axis = normalize((1.0, -1.0, 0.0))

        t_min, t_max = bbox_axial_extent(bbox_min, bbox_max, origin, axis)

        # True max = (10, 0, _) projected = (10*1 + 0*(-1))/sqrt(2) = 10/sqrt(2)
        # True min = (0, 20, _) projected = (0*1 + 20*(-1))/sqrt(2) = -20/sqrt(2)
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        expected_max = 10.0 * inv_sqrt2
        expected_min = -20.0 * inv_sqrt2

        assert abs(t_max - expected_max) < 1e-6
        assert abs(t_min - expected_min) < 1e-6

        # Verify 2-corner approach gives WRONG result:
        # proj(minPoint=(0,0,0)) = 0
        # proj(maxPoint=(10,20,5)) = (10-20)/sqrt(2) = -10/sqrt(2)
        # 2-corner would give min=-10/sqrt(2), max=0 — both wrong!
        two_corner_max = max(0.0, -10.0 * inv_sqrt2)
        assert two_corner_max != pytest.approx(expected_max, abs=1e-6), (
            "2-corner approach should NOT give the correct max"
        )

    def test_negative_axis_direction(self):
        """Fully negative axis direction."""
        bbox_min = (0.0, 0.0, 0.0)
        bbox_max = (10.0, 10.0, 10.0)
        origin = (5.0, 5.0, 5.0)
        axis = normalize((-1.0, -1.0, -1.0))

        t_min, t_max = bbox_axial_extent(bbox_min, bbox_max, origin, axis)

        # max projection: corner (0,0,0) → (-5,-5,-5)·(-1,-1,-1)/sqrt(3) = 15/sqrt(3)
        # min projection: corner (10,10,10) → (5,5,5)·(-1,-1,-1)/sqrt(3) = -15/sqrt(3)
        inv_sqrt3 = 1.0 / math.sqrt(3.0)
        assert abs(t_max - 15.0 * inv_sqrt3) < 1e-6
        assert abs(t_min - (-15.0 * inv_sqrt3)) < 1e-6

    def test_origin_offset(self):
        """Origin not at zero — projections are relative to axis origin."""
        bbox_min = (10.0, 10.0, 10.0)
        bbox_max = (20.0, 20.0, 20.0)
        origin = (15.0, 15.0, 15.0)
        axis = (1.0, 0.0, 0.0)

        t_min, t_max = bbox_axial_extent(bbox_min, bbox_max, origin, axis)
        assert abs(t_min - (-5.0)) < 1e-10
        assert abs(t_max - 5.0) < 1e-10

    def test_degenerate_zero_volume_bbox(self):
        """Point bbox (zero volume) — min and max projections are equal."""
        point = (5.0, 3.0, 7.0)
        origin = (0.0, 0.0, 0.0)
        axis = (1.0, 0.0, 0.0)

        t_min, t_max = bbox_axial_extent(point, point, origin, axis)
        assert abs(t_min - 5.0) < 1e-10
        assert abs(t_max - 5.0) < 1e-10

    def test_real_world_tube_angle(self):
        """Realistic tube axis matching the driver shock hoop bug scenario.

        Axis ≈ (-0.45, -0.01, -0.89) — the tube that triggered the bug
        where cope endpoints were calculated 14cm off because only 2 bbox
        corners were projected.
        """
        # Tube runs from roughly (33, 109, -6) to (70, 110, 68)
        # Single cylinder face bbox (approximate)
        bbox_min = (33.0, 107.0, -6.0)
        bbox_max = (70.0, 111.0, 68.0)
        origin = (50.0, 109.0, 30.0)
        axis = normalize((-0.4463, -0.0085, -0.8948))

        t_min, t_max = bbox_axial_extent(bbox_min, bbox_max, origin, axis)

        # The tube is ~82cm long diagonally.  The axial extent should be
        # at least as large as the tube length along the axis.
        extent = t_max - t_min
        tube_length_approx = math.sqrt(
            (70 - 33) ** 2 + (111 - 107) ** 2 + (68 + 6) ** 2
        )
        assert extent >= tube_length_approx * 0.9, (
            f"Axial extent {extent:.1f} too small for ~{tube_length_approx:.1f}cm tube"
        )
