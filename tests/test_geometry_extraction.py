"""
Tests for geometry extraction module - runs without Fusion.

Run with: pytest tests/ -v
"""
from __future__ import annotations

from dataclasses import dataclass

from core.geometry_extraction import determine_primary_axis, get_free_endpoint
from models.types import ElementType, Point3D


@dataclass
class MockPathElement:
    """Mock PathElement for testing without Fusion API."""

    element_type: ElementType
    endpoints: tuple[Point3D, Point3D]
    entity: None = None  # Not needed for these tests


class TestDeterminePrimaryAxis:
    """Test determine_primary_axis() function."""

    # Happy path - positive directions
    def test_primary_axis_x_positive(self) -> None:
        """X-axis positive direction detected."""
        start = (0.0, 0.0, 0.0)
        end = (10.0, 1.0, 0.5)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'X'
        assert idx == 0
        assert current == '+X'
        assert opposite == '-X'

    def test_primary_axis_y_positive(self) -> None:
        """Y-axis positive direction detected."""
        start = (0.0, 0.0, 0.0)
        end = (1.0, 10.0, 0.5)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'Y'
        assert idx == 1
        assert current == '+Y'
        assert opposite == '-Y'

    def test_primary_axis_z_positive(self) -> None:
        """Z-axis positive direction detected."""
        start = (0.0, 0.0, 0.0)
        end = (1.0, 0.5, 10.0)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'Z'
        assert idx == 2
        assert current == '+Z'
        assert opposite == '-Z'

    # Happy path - negative directions
    def test_primary_axis_x_negative(self) -> None:
        """X-axis negative direction detected."""
        start = (10.0, 0.0, 0.0)
        end = (0.0, 1.0, 0.5)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'X'
        assert idx == 0
        assert current == '-X'
        assert opposite == '+X'

    def test_primary_axis_y_negative(self) -> None:
        """Y-axis negative direction detected."""
        start = (0.0, 10.0, 0.0)
        end = (1.0, 0.0, 0.5)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'Y'
        assert idx == 1
        assert current == '-Y'
        assert opposite == '+Y'

    def test_primary_axis_z_negative(self) -> None:
        """Z-axis negative direction detected."""
        start = (0.0, 0.0, 10.0)
        end = (1.0, 0.5, 0.0)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'Z'
        assert idx == 2
        assert current == '-Z'
        assert opposite == '+Z'

    # Defensive: Edge cases
    def test_zero_displacement_returns_x(self) -> None:
        """Zero displacement defaults to X axis."""
        start = (5.0, 5.0, 5.0)
        end = (5.0, 5.0, 5.0)  # Same point
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'X'
        assert idx == 0
        # Direction is arbitrary for zero displacement (returns -X)
        assert current in ('+X', '-X')

    def test_tie_between_x_and_y(self) -> None:
        """When X and Y are equal, X takes priority."""
        start = (0.0, 0.0, 0.0)
        end = (10.0, 10.0, 0.0)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        # X is checked first, so X wins on tie
        assert axis == 'X'
        assert idx == 0

    def test_tie_between_y_and_z(self) -> None:
        """When Y and Z are equal (and larger than X), Y takes priority."""
        start = (0.0, 0.0, 0.0)
        end = (0.0, 10.0, 10.0)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        # Y is checked before Z
        assert axis == 'Y'
        assert idx == 1

    def test_all_three_equal(self) -> None:
        """When all displacements equal, X takes priority."""
        start = (0.0, 0.0, 0.0)
        end = (5.0, 5.0, 5.0)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'X'
        assert idx == 0

    def test_very_small_displacement(self) -> None:
        """Very small displacements are handled correctly."""
        start = (0.0, 0.0, 0.0)
        end = (0.0001, 0.00001, 0.000001)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'X'
        assert current == '+X'

    def test_large_displacement(self) -> None:
        """Large displacements are handled correctly."""
        start = (0.0, 0.0, 0.0)
        end = (1000000.0, 500000.0, 100000.0)
        axis, idx, current, opposite = determine_primary_axis(start, end)
        assert axis == 'X'
        assert current == '+X'


class TestGetFreeEndpoint:
    """Test get_free_endpoint() function."""

    # Happy path tests
    def test_finds_unconnected_endpoint_at_start(self) -> None:
        """First element's start is free endpoint of chain."""
        e1 = MockPathElement('line', ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
        e2 = MockPathElement('arc', ((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
        elements = [e1, e2]

        # e1's start (0,0,0) is not connected to e2
        result = get_free_endpoint(e1, elements)
        assert result == (0.0, 0.0, 0.0)

    def test_finds_unconnected_endpoint_at_end(self) -> None:
        """Last element's end is free endpoint of chain."""
        e1 = MockPathElement('line', ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
        e2 = MockPathElement('arc', ((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
        elements = [e1, e2]

        # e2's end (2,0,0) is not connected to e1
        result = get_free_endpoint(e2, elements)
        assert result == (2.0, 0.0, 0.0)

    def test_middle_element_has_no_free_endpoint(self) -> None:
        """Middle element returns its first endpoint as fallback."""
        e1 = MockPathElement('line', ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
        e2 = MockPathElement('arc', ((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
        e3 = MockPathElement('line', ((2.0, 0.0, 0.0), (3.0, 0.0, 0.0)))
        elements = [e1, e2, e3]

        # e2 is connected at both ends, returns its start as fallback
        result = get_free_endpoint(e2, elements)
        assert result == (1.0, 0.0, 0.0)

    # Defensive: Edge cases
    def test_single_element_returns_start(self) -> None:
        """Single element returns its start endpoint."""
        e1 = MockPathElement('line', ((5.0, 0.0, 0.0), (10.0, 0.0, 0.0)))
        elements = [e1]

        # Both endpoints are free, returns start (first one checked)
        result = get_free_endpoint(e1, elements)
        assert result == (5.0, 0.0, 0.0)

    def test_disconnected_element_returns_start(self) -> None:
        """Disconnected element returns its start endpoint."""
        e1 = MockPathElement('line', ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
        e2 = MockPathElement('line', ((100.0, 100.0, 100.0), (101.0, 100.0, 100.0)))
        elements = [e1, e2]

        # e2 is completely disconnected from e1
        result = get_free_endpoint(e2, elements)
        assert result == (100.0, 100.0, 100.0)

    def test_both_endpoints_connected_returns_first(self) -> None:
        """When both endpoints are connected, returns first endpoint."""
        # Create a closed triangle
        e1 = MockPathElement('line', ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
        e2 = MockPathElement('arc', ((1.0, 0.0, 0.0), (0.5, 0.866, 0.0)))
        e3 = MockPathElement('line', ((0.5, 0.866, 0.0), (0.0, 0.0, 0.0)))
        elements = [e1, e2, e3]

        # e1 is connected at both ends (to e3 at start, to e2 at end)
        result = get_free_endpoint(e1, elements)
        assert result == (0.0, 0.0, 0.0)  # Falls back to first endpoint

    def test_empty_other_elements_returns_start(self) -> None:
        """Element with no others returns its start."""
        e1 = MockPathElement('line', ((3.0, 4.0, 5.0), (6.0, 7.0, 8.0)))
        elements = [e1]  # Only itself

        result = get_free_endpoint(e1, elements)
        assert result == (3.0, 4.0, 5.0)

    def test_connection_within_tolerance(self) -> None:
        """Elements within tolerance (0.1 cm) are considered connected."""
        e1 = MockPathElement('line', ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
        # e2 starts at 1.05, within 0.1 cm tolerance
        e2 = MockPathElement('arc', ((1.05, 0.0, 0.0), (2.0, 0.0, 0.0)))
        elements = [e1, e2]

        # e1's end (1,0,0) is close to e2's start (1.05,0,0) - within tolerance
        # So e1's start should be the free endpoint
        result = get_free_endpoint(e1, elements)
        assert result == (0.0, 0.0, 0.0)

    def test_long_chain_finds_correct_endpoint(self) -> None:
        """Correctly identifies free endpoint in a long chain."""
        e1 = MockPathElement('line', ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)))
        e2 = MockPathElement('arc', ((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
        e3 = MockPathElement('line', ((2.0, 0.0, 0.0), (3.0, 0.0, 0.0)))
        e4 = MockPathElement('arc', ((3.0, 0.0, 0.0), (4.0, 0.0, 0.0)))
        e5 = MockPathElement('line', ((4.0, 0.0, 0.0), (5.0, 0.0, 0.0)))
        elements = [e1, e2, e3, e4, e5]

        # First element's start is free
        assert get_free_endpoint(e1, elements) == (0.0, 0.0, 0.0)
        # Last element's end is free
        assert get_free_endpoint(e5, elements) == (5.0, 0.0, 0.0)
        # Middle elements return first endpoint as fallback
        assert get_free_endpoint(e3, elements) == (2.0, 0.0, 0.0)
