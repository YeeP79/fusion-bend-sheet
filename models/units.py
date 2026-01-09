"""Unit configuration for Fusion 360 designs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import adsk.fusion


# Valid precision values
VALID_PRECISIONS_IMPERIAL: tuple[int, ...] = (0, 4, 8, 16, 32)
VALID_PRECISIONS_METRIC: tuple[int, ...] = (0, 1, 2, 5, 10)

DEFAULT_PRECISION_IMPERIAL: int = 16
DEFAULT_PRECISION_METRIC: int = 1


@dataclass(slots=True)
class UnitConfig:
    """
    Unit configuration extracted from Fusion design.
    
    Attributes:
        is_metric: True if using metric units
        unit_name: Unit name ('in', 'mm', 'cm', 'm', 'ft')
        unit_symbol: Display symbol ('"', 'mm', 'cm', 'm', "'")
        cm_to_unit: Conversion factor from internal cm to display unit
        default_tube_od: Default tube OD string for this unit
        default_precision: Default precision value
        valid_precisions: Valid precision options
    """
    is_metric: bool
    unit_name: str
    unit_symbol: str
    cm_to_unit: float
    default_tube_od: str
    default_precision: int
    valid_precisions: tuple[int, ...]
    
    @classmethod
    def from_design(cls, design: 'adsk.fusion.Design') -> UnitConfig:
        """
        Extract unit configuration from Fusion design.
        
        Args:
            design: The active Fusion design
            
        Returns:
            UnitConfig with appropriate settings for the design's units
        """
        units_mgr = design.unitsManager
        default_units = units_mgr.defaultLengthUnits
        
        # Map Fusion unit strings to our config
        unit_configs = {
            'in': cls(
                is_metric=False,
                unit_name='in',
                unit_symbol='"',
                cm_to_unit=1.0 / 2.54,
                default_tube_od='1.75',
                default_precision=DEFAULT_PRECISION_IMPERIAL,
                valid_precisions=VALID_PRECISIONS_IMPERIAL
            ),
            'ft': cls(
                is_metric=False,
                unit_name='ft',
                unit_symbol="'",
                cm_to_unit=1.0 / 30.48,
                default_tube_od='0.146',
                default_precision=DEFAULT_PRECISION_IMPERIAL,
                valid_precisions=VALID_PRECISIONS_IMPERIAL
            ),
            'mm': cls(
                is_metric=True,
                unit_name='mm',
                unit_symbol='mm',
                cm_to_unit=10.0,
                default_tube_od='44.45',
                default_precision=DEFAULT_PRECISION_METRIC,
                valid_precisions=VALID_PRECISIONS_METRIC
            ),
            'cm': cls(
                is_metric=True,
                unit_name='cm',
                unit_symbol='cm',
                cm_to_unit=1.0,
                default_tube_od='4.445',
                default_precision=DEFAULT_PRECISION_METRIC,
                valid_precisions=VALID_PRECISIONS_METRIC
            ),
            'm': cls(
                is_metric=True,
                unit_name='m',
                unit_symbol='m',
                cm_to_unit=0.01,
                default_tube_od='0.04445',
                default_precision=DEFAULT_PRECISION_METRIC,
                valid_precisions=VALID_PRECISIONS_METRIC
            ),
        }
        
        config = unit_configs.get(default_units)
        if config is None:
            supported = ", ".join(sorted(unit_configs.keys()))
            raise ValueError(
                f"Unsupported unit system: '{default_units}'. "
                f"Supported units: {supported}"
            )
        return config
