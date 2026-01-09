"""
Tests for calculations module - runs without Fusion.

Run with: pytest tests/ -v
"""
from dataclasses import dataclass

from core.calculations import build_segments_and_marks, validate_clr_consistency
from models import BendData, StraightSection


@dataclass
class MockArc:
    """Mock SketchArc that only provides radius attribute."""
    radius: float


@dataclass
class MockUnitConfig:
    """Mock UnitConfig for testing."""
    cm_to_unit: float = 1.0  # 1:1 for simplicity in tests


class TestValidateClrConsistency:
    """Test CLR validation function."""

    # Happy path tests
    def test_single_arc(self) -> None:
        arcs = [MockArc(radius=5.0)]
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 5.0
        assert has_mismatch is False
        assert values == [5.0]

    def test_multiple_matching_arcs(self) -> None:
        arcs = [MockArc(radius=5.0), MockArc(radius=5.0), MockArc(radius=5.0)]
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 5.0
        assert has_mismatch is False

    def test_arcs_within_tolerance(self) -> None:
        # 0.2% of 5.0 is 0.01, so 5.005 should be within tolerance
        arcs = [MockArc(radius=5.0), MockArc(radius=5.005)]
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 5.0
        assert has_mismatch is False

    def test_arcs_outside_tolerance(self) -> None:
        # 5.0 and 5.1 differ by 0.1, which is 2% - way outside 0.2% tolerance
        arcs = [MockArc(radius=5.0), MockArc(radius=5.1)]
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 5.0
        assert has_mismatch is True

    # Empty list tests
    def test_empty_arcs_list(self) -> None:
        arcs: list[MockArc] = []
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 0.0
        assert has_mismatch is False
        assert values == []

    # Issue 4 fix: Zero/negative CLR tests
    def test_zero_clr_returns_mismatch(self) -> None:
        """Zero CLR should return mismatch flag (Issue 4 fix)."""
        arcs = [MockArc(radius=0.0)]
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 0.0
        assert has_mismatch is True
        assert values == [0.0]

    def test_negative_clr_returns_mismatch(self) -> None:
        """Negative CLR should return mismatch flag (Issue 4 fix)."""
        arcs = [MockArc(radius=-1.0)]
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 0.0
        assert has_mismatch is True
        assert values == [-1.0]

    def test_multiple_arcs_first_zero(self) -> None:
        """If first arc has zero radius, should return mismatch."""
        arcs = [MockArc(radius=0.0), MockArc(radius=5.0)]
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 0.0
        assert has_mismatch is True

    # Unit conversion tests
    def test_unit_conversion(self) -> None:
        # Simulating inches: 1 inch = 2.54 cm, so cm_to_unit = 1/2.54
        arcs = [MockArc(radius=2.54)]  # 2.54 cm = 1 inch
        units = MockUnitConfig(cm_to_unit=1 / 2.54)
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert abs(clr - 1.0) < 0.0001  # Should be 1 inch
        assert has_mismatch is False

    # Minimum tolerance floor tests
    def test_very_small_clr_uses_minimum_tolerance(self) -> None:
        """Very small CLR should use minimum tolerance floor of 0.001."""
        # With CLR = 0.01, ratio tolerance = 0.00002 (too small)
        # Should use minimum floor of 0.001 instead
        arcs = [MockArc(radius=0.01), MockArc(radius=0.0105)]
        units = MockUnitConfig()
        clr, has_mismatch, values = validate_clr_consistency(arcs, units)
        assert clr == 0.01
        # 0.0005 difference is within 0.001 tolerance floor
        assert has_mismatch is False


# Helper function to create StraightSection objects
def make_straight(num: int, length: float) -> StraightSection:
    """Create a StraightSection for testing."""
    return StraightSection(
        number=num,
        length=length,
        start=(0.0, 0.0, 0.0),
        end=(length, 0.0, 0.0),
        vector=(length, 0.0, 0.0),
    )


class TestBuildSegmentsAndMarks:
    """Test build_segments_and_marks() function."""

    # Happy path tests
    def test_single_bend_path(self) -> None:
        """Simple path: straight -> bend -> straight."""
        straights = [make_straight(1, 10.0), make_straight(2, 10.0)]
        bends = [BendData(number=1, angle=45.0, rotation=None, arc_length=5.0)]

        segments, marks = build_segments_and_marks(
            straights, bends, extra_material=2.0, die_offset=0.5
        )

        # Should have 3 segments: straight, bend, straight
        assert len(segments) == 3

        # Check segment order and types
        assert segments[0].segment_type == 'straight'
        assert segments[0].name == 'Straight 1'
        assert segments[1].segment_type == 'bend'
        assert segments[1].name == 'BEND 1'
        assert segments[2].segment_type == 'straight'
        assert segments[2].name == 'Straight 2'

        # Check cumulative positions
        assert segments[0].starts_at == 2.0  # extra_material
        assert segments[0].ends_at == 12.0  # 2 + 10
        assert segments[1].starts_at == 12.0
        assert segments[1].ends_at == 17.0  # 12 + 5
        assert segments[2].starts_at == 17.0
        assert segments[2].ends_at == 27.0  # 17 + 10

        # Check mark position
        assert len(marks) == 1
        assert marks[0].bend_num == 1
        assert marks[0].mark_position == 11.5  # 12 - 0.5 (die_offset)
        assert marks[0].bend_angle == 45.0

    def test_multi_bend_path(self) -> None:
        """Path with multiple bends."""
        straights = [
            make_straight(1, 10.0),
            make_straight(2, 8.0),
            make_straight(3, 12.0),
        ]
        bends = [
            BendData(number=1, angle=45.0, rotation=None, arc_length=4.0),
            BendData(number=2, angle=90.0, rotation=30.0, arc_length=6.0),
        ]

        segments, marks = build_segments_and_marks(
            straights, bends, extra_material=0.0, die_offset=1.0
        )

        # Should have 5 segments
        assert len(segments) == 5
        assert segments[0].segment_type == 'straight'
        assert segments[1].segment_type == 'bend'
        assert segments[2].segment_type == 'straight'
        assert segments[3].segment_type == 'bend'
        assert segments[4].segment_type == 'straight'

        # Check mark positions
        assert len(marks) == 2
        assert marks[0].bend_num == 1
        assert marks[0].mark_position == 9.0  # 10 - 1 (die_offset)
        assert marks[1].bend_num == 2
        assert marks[1].mark_position == 21.0  # (10 + 4 + 8) - 1

    # Defensive: Edge cases
    def test_empty_bends(self) -> None:
        """Path with no bends (just straights)."""
        straights = [make_straight(1, 10.0), make_straight(2, 10.0)]
        bends: list[BendData] = []

        segments, marks = build_segments_and_marks(
            straights, bends, extra_material=0.0, die_offset=0.0
        )

        # Should have 2 straight segments only
        assert len(segments) == 2
        assert all(s.segment_type == 'straight' for s in segments)
        assert len(marks) == 0

    def test_zero_extra_material(self) -> None:
        """Path with no extra material at start."""
        straights = [make_straight(1, 10.0), make_straight(2, 10.0)]
        bends = [BendData(number=1, angle=45.0, rotation=None, arc_length=5.0)]

        segments, marks = build_segments_and_marks(
            straights, bends, extra_material=0.0, die_offset=0.5
        )

        # First segment should start at 0
        assert segments[0].starts_at == 0.0

    def test_zero_die_offset(self) -> None:
        """Path with zero die offset."""
        straights = [make_straight(1, 10.0), make_straight(2, 10.0)]
        bends = [BendData(number=1, angle=45.0, rotation=None, arc_length=5.0)]

        segments, marks = build_segments_and_marks(
            straights, bends, extra_material=2.0, die_offset=0.0
        )

        # Mark should be at bend start (no offset)
        assert marks[0].mark_position == 12.0  # 2 + 10, no offset

    def test_very_small_lengths(self) -> None:
        """Handle very small lengths without precision issues."""
        straights = [make_straight(1, 0.001), make_straight(2, 0.001)]
        bends = [BendData(number=1, angle=45.0, rotation=None, arc_length=0.0005)]

        segments, marks = build_segments_and_marks(
            straights, bends, extra_material=0.0, die_offset=0.0001
        )

        # Should complete without errors
        assert len(segments) == 3
        assert len(marks) == 1
        # Verify precision is maintained
        assert abs(segments[0].ends_at - 0.001) < 1e-10

    def test_cumulative_position_accuracy(self) -> None:
        """Verify cumulative positions are calculated correctly."""
        straights = [
            make_straight(1, 5.0),
            make_straight(2, 7.0),
            make_straight(3, 3.0),
        ]
        bends = [
            BendData(number=1, angle=45.0, rotation=None, arc_length=2.0),
            BendData(number=2, angle=90.0, rotation=15.0, arc_length=4.0),
        ]

        segments, marks = build_segments_and_marks(
            straights, bends, extra_material=1.0, die_offset=0.0
        )

        # Verify total length
        # Extra: 1, S1: 5, B1: 2, S2: 7, B2: 4, S3: 3 = 22 total
        assert segments[-1].ends_at == 22.0

        # Verify each segment connects to the next
        for i in range(len(segments) - 1):
            assert segments[i].ends_at == segments[i + 1].starts_at

    def test_rotation_on_segments(self) -> None:
        """Verify rotation is set correctly on straight segments."""
        straights = [
            make_straight(1, 10.0),
            make_straight(2, 10.0),
            make_straight(3, 10.0),
        ]
        bends = [
            BendData(number=1, angle=45.0, rotation=None, arc_length=5.0),  # First - no rotation
            BendData(number=2, angle=90.0, rotation=30.0, arc_length=5.0),  # Has rotation
        ]

        segments, marks = build_segments_and_marks(
            straights, bends, extra_material=0.0, die_offset=0.0
        )

        # First straight has rotation from first bend (None)
        assert segments[0].rotation is None
        # Second straight has rotation from second bend (30.0)
        assert segments[2].rotation == 30.0
        # Third straight has no following bend, so rotation is None
        assert segments[4].rotation is None

        # Bend segments should have no rotation set
        assert segments[1].rotation is None
        assert segments[3].rotation is None
