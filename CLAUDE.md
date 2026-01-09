# Claude Code Development Standards

**Project:** TubeBendSheet - Autodesk Fusion Add-in for Tube Bend Rotation Calculation
**Last Updated:** 2026-01-09
**Applies to:** All AI assistants, developers, and code reviewers

---

## Core Principles

This project follows **strict Python type safety** and **SOLID programming principles**. Code quality is non-negotiable.

**Why this matters:** This add-in helps fabricators build real parts. A wrong rotation angle means wasted material. Type safety and careful calculations are requirements, not suggestions.

---

## Project Overview

An Autodesk Fusion add-in that calculates multi-plane tube bend rotations using the vector cross product method, generates printable bend sheets, and manages bender/die profiles with document-level persistence.

**Key Features:**
- Calculate rotation angles between bend planes
- Generate HTML bend sheets for printing
- Manage bender profiles with dies (CLR, offset, tube OD)
- Save settings per-sketch using Fusion document attributes
- Support imperial and metric units from design settings

---

## Definition of Done

Code is **NOT considered complete** until all of the following pass:

### 1. Syntax Check Passes

```bash
make check
```

**Requirements:**
- Zero Python syntax errors
- All files compile cleanly

### 2. Linting Passes

```bash
make lint
```

**Requirements:**
- Zero critical linting errors
- No unused imports in production code
- Consistent code style

### 3. Type Checking Passes

```bash
make typecheck
```

**Requirements:**
- Zero pyright errors on core/, models/, storage/
- All functions have type hints
- No `Any` types without justification

### 4. Tests Pass

```bash
make test
```

**Requirements:**
- All unit tests passing
- Tests cover edge cases and error conditions
- No skipped tests without justification

### 5. Full Validation

```bash
make validate          # Runs check, lint, test
make typecheck         # Run separately - type checking
```

The `validate` target runs syntax check, linting, and tests. Run `make typecheck` separately for type checking. **Use both before every commit.**

---

## Type Safety Requirements

### Always Use Type Hints

```python
# WRONG
def calculate_rotation(n1, n2):
    cos_theta = dot_product(n1, n2) / (magnitude(n1) * magnitude(n2))
    return math.degrees(math.acos(cos_theta))

# CORRECT
def calculate_rotation(n1: Vector3D, n2: Vector3D) -> float:
    """Calculate rotation angle between two bend plane normals."""
    cos_theta: float = dot_product(n1, n2) / (magnitude(n1) * magnitude(n2))
    cos_theta = max(-1.0, min(1.0, cos_theta))  # Clamp for floating point
    return math.degrees(math.acos(cos_theta))
```

### Avoid `Any` Type

```python
# WRONG - Defeats type checking
def process_data(data: Any) -> None:
    ...

# CORRECT - Use specific types or unions
def process_data(data: dict[str, str] | list[str]) -> None:
    ...

# CORRECT - Use TypeVar for generics
T = TypeVar('T')
def process_item(item: T) -> T:
    ...
```

### Use Type Aliases

Type aliases are defined in `models/types.py`:

```python
# From models/types.py
Vector3D = tuple[float, float, float]
Point3D = tuple[float, float, float]
ElementType = Literal["line", "arc"]
SegmentType = Literal["straight", "bend"]
```

Import and use them:
```python
from models.types import Vector3D, Point3D
```

### Use Dataclasses for Structured Data

```python
@dataclass
class BendData:
    """Represents a bend in the tube path."""
    number: int
    angle: float  # Degrees
    rotation: float | None  # Degrees, None for first bend
    arc_length: float = 0.0
```

### Handle Optional Types Explicitly

```python
def get_die_by_id(self, die_id: str) -> Die | None:
    """Find a die by its ID."""
    for die in self.dies:
        if die.id == die_id:
            return die
    return None
```

---

## SOLID Principles

### S - Single Responsibility Principle

**Rule:** Each class/function should have ONE reason to change.

```python
# WRONG - Multiple responsibilities
class BendCalculator:
    def calculate_angles(self): ...
    def format_output(self): ...
    def save_to_file(self): ...
    def load_settings(self): ...

# CORRECT - Separate responsibilities
class BendCalculator:
    """Only calculates bend angles and rotations."""
    def calculate_angles(self, path: list[PathElement]) -> list[BendData]: ...

class BendSheetFormatter:
    """Only formats bend data for display."""
    def format_length(self, value: float, units: UnitConfig) -> str: ...

class ProfileManager:
    """Only manages bender profile persistence."""
    def load(self) -> None: ...
    def save(self) -> None: ...
```

**In this project:**
- `core/calculations.py` - Only bend calculations
- `core/formatting.py` - Only string formatting
- `core/html_generator.py` - Only HTML output
- `storage/profiles.py` - Only file I/O for profiles
- `models/` - Only data structures

### O - Open/Closed Principle

**Rule:** Open for extension, closed for modification.

```python
# WRONG - Must modify to add new formats
def format_length(value: float, format_type: str) -> str:
    if format_type == 'imperial':
        return f'{value}"'
    elif format_type == 'metric':
        return f'{value}mm'
    # Must modify for each new format

# CORRECT - Extend via UnitConfig
def format_length(value: float, precision: int, units: UnitConfig) -> str:
    """Format using unit configuration - new units just need new UnitConfig."""
    return units.format(value, precision)
```

### L - Liskov Substitution Principle

**Rule:** Subtypes must be substitutable for their base types.

```python
# CORRECT - All path elements can be processed uniformly
@dataclass
class PathElement:
    element_type: Literal['line', 'arc']
    entity: SketchLine | SketchArc

def process_path(elements: list[PathElement]) -> None:
    for element in elements:
        # Works for any PathElement regardless of type
        start = get_start_point(element)
        end = get_end_point(element)
```

### I - Interface Segregation Principle

**Rule:** Don't force clients to depend on interfaces they don't use.

```python
# WRONG - Bloated class
class BenderService:
    def load_benders(self): ...
    def save_benders(self): ...
    def calculate_bend(self): ...
    def format_output(self): ...
    def generate_html(self): ...

# CORRECT - Focused classes
class ProfileManager:
    """Only profile operations."""
    def load(self) -> None: ...
    def save(self) -> None: ...

class BendCalculator:
    """Only calculations."""
    def calculate(self, path: list[PathElement]) -> BendResult: ...
```

### D - Dependency Inversion Principle

**Rule:** Depend on abstractions, not concretions.

```python
# WRONG - Hard dependency on file system
class ProfileManager:
    def load(self):
        with open('/path/to/benders.json') as f:
            return json.load(f)

# CORRECT - Path injected
class ProfileManager:
    def __init__(self, addin_path: str):
        self._profiles_path = Path(addin_path) / 'resources' / 'benders.json'

    def load(self) -> None:
        # Uses injected path
        ...
```

---

## Testing Standards

### Testing Philosophy: Defensive Programming First

**Primary Goal:** Find weaknesses through adversarial testing.
**Secondary Goal:** Cover all logic paths in the codebase.
**Tertiary Goal:** Meet coverage thresholds.

### Test Priorities (In Order)

1. **Defensive Programming Tests** - Attack the code to find weaknesses
   - Invalid inputs (None, empty strings, wrong types)
   - Boundary conditions (empty lists, single items, maximum values)
   - Floating point edge cases (NaN, infinity, precision limits)
   - Malformed data (invalid JSON, missing fields)

2. **Logic Path Coverage** - Ensure all code paths execute
   - All branches (if/else)
   - All error handlers
   - All early returns
   - All conditional logic combinations

3. **Coverage Metrics** - Quantitative measurement
   - Target 80%+ line coverage on core/, models/, storage/
   - 100% coverage on critical calculation functions

### Defensive Test Categories

```python
class TestBenderModel:
    """Test Bender and Die dataclass functionality."""

    # Happy path tests
    def test_bender_creation(self):
        bender = Bender(id="test", name="Test", min_grip=6.0)
        assert bender.name == "Test"

    # Defensive: Invalid inputs
    def test_bender_empty_name(self):
        bender = Bender(id="test", name="", min_grip=6.0)
        assert bender.name == ""  # Should handle gracefully

    def test_die_negative_clr(self):
        die = Die(id="1", name="Test", tube_od=1.5, clr=-1.0, offset=0.5)
        # Document expected behavior for invalid input

    # Defensive: Boundary conditions
    def test_die_matches_clr_exact(self):
        die = Die(id="1", name="Test", tube_od=1.5, clr=4.5, offset=0.5)
        assert die.matches_clr(4.5, tolerance=0.1) == True

    def test_die_matches_clr_at_tolerance_boundary(self):
        die = Die(id="1", name="Test", tube_od=1.5, clr=4.5, offset=0.5)
        assert die.matches_clr(4.6, tolerance=0.1) == True  # Exactly at boundary
        assert die.matches_clr(4.61, tolerance=0.1) == False  # Just outside

    # Defensive: Floating point
    def test_calculation_precision(self):
        """Ensure floating point doesn't cause NaN or overflow."""
        # Test with very small angles
        result = calculate_rotation((1, 0, 0), (0.9999999, 0.0001, 0))
        assert not math.isnan(result)

        # Test with parallel vectors (0 degree)
        result = calculate_rotation((1, 0, 0), (1, 0, 0))
        assert abs(result) < 0.001

    # Logic path: JSON roundtrip
    def test_bender_json_roundtrip(self):
        original = Bender(id="b1", name="Test", min_grip=6.0, dies=[
            Die(id="d1", name="Die", tube_od=1.5, clr=4.5, offset=0.5)
        ])
        data = original.to_dict()
        restored = Bender.from_dict(data)
        assert restored.name == original.name
        assert len(restored.dies) == len(original.dies)
```

### What NOT to Do

```python
# WRONG - Only testing happy path
def test_save():
    bender = Bender(id="1", name="Test", min_grip=6.0)
    assert bender is not None  # Useless test

# WRONG - Not checking actual values
def test_calculation():
    result = calculate_bend_angle(arc)
    assert result  # Truthy check tells us nothing

# WRONG - Ignoring edge cases
def test_format_length():
    assert format_length(5.5, 16, units) == "5 1/2\""
    # Missing: 0, negative, very large, fractional precision edge cases

# CORRECT - Specific value assertions
def test_format_length_imperial():
    units = UnitConfig(is_metric=False, ...)
    assert format_length(5.5, 16, units) == '5 1/2"'
    assert format_length(0, 16, units) == '0"'
    assert format_length(0.0625, 16, units) == '1/16"'
```

---

## Directory Structure

```
TubeBendSheet/
├── TubeBendSheet.py               # Main entry point (run/stop)
├── TubeBendSheet.manifest         # Add-in metadata
├── config.py                      # Global configuration
├── Makefile                       # Development tasks
├── pyproject.toml                 # Python project config (ruff, pyright, pytest)
├── commands/                      # UI command handlers (Heavy Fusion deps)
│   ├── __init__.py
│   ├── createBendSheet/           # Bend sheet generation command
│   │   ├── entry.py               # Command entry point
│   │   ├── bend_sheet_generator.py
│   │   ├── dialog_builder.py
│   │   ├── input_parser.py
│   │   └── selection_validator.py
│   └── manageBenders/             # Bender profile management
│       ├── entry.py
│       ├── bender_editor.py
│       ├── html_bridge.py
│       └── input_dialogs.py
├── lib/fusionAddInUtils/          # Handler management, logging
├── core/                          # Pure calculation logic (No Fusion deps)
│   ├── geometry.py                # Vector math (cross product, magnitude)
│   ├── geometry_extraction.py     # Extract geometry from Fusion entities
│   ├── path_analysis.py           # Analyze path connectivity
│   ├── path_ordering.py           # Order geometry into valid path
│   ├── calculations.py            # Bend/rotation calculations
│   ├── formatting.py              # Length/angle formatting
│   └── html_generator.py          # Bend sheet HTML generation
├── models/                        # Data structures (No Fusion deps)
│   ├── types.py                   # Type aliases (Vector3D, Point3D)
│   ├── bender.py                  # Bender/Die dataclasses
│   ├── bend_data.py               # BendData, PathSegment, etc.
│   └── units.py                   # UnitConfig for unit conversion
├── storage/                       # Persistence layer
│   ├── profiles.py                # JSON file storage for bender profiles
│   └── attributes.py              # Fusion document attributes
├── tests/                         # Unit tests (pytest)
├── typings/adsk/                  # Type stubs for Fusion API
└── resources/benders.json         # Saved bender profiles
```

### Layer Rules

| Layer | Fusion API | Testable Standalone |
|-------|------------|---------------------|
| `commands/` | Heavy | No |
| `core/` | None | Yes |
| `models/` | None | Yes |
| `storage/profiles.py` | None | Yes |
| `storage/attributes.py` | Yes | No |

**Rule:** Keep `core/` and `models/` free of Fusion API calls. This enables unit testing.

---

## Autodesk Fusion Specific Guidelines

### Handler Lifetime Management

**Critical:** Fusion garbage-collects event handlers unless you keep references.

```python
# Usage in commands
futil.add_handler(cmd_def.commandCreated, command_created)
futil.add_handler(cmd.execute, command_execute)
```

### Unit Conversion

**Rule:** Fusion stores all geometry in centimeters internally.

```python
# WRONG - Assuming inches
length = line.length  # This is in cm!

# CORRECT - Convert using UnitConfig
units = UnitConfig.from_design(design)
length_display = line.length * units.cm_to_unit
```

### Error Handling

```python
def command_execute(args: adsk.core.CommandEventArgs):
    try:
        # ... command logic ...
    except:
        futil.handle_error('command_execute')
```

---

## Common Pitfalls

### 1. Bare Except Without Logging

```python
# WRONG
except:
    pass

# CORRECT
except:
    futil.handle_error('function_name')
```

### 2. Assuming Selection Order

```python
# WRONG - User clicks in arbitrary order
lines = [sel for sel in selections if isinstance(sel, SketchLine)]

# CORRECT - Build ordered path from connectivity
ordered = build_ordered_path(elements)
```

### 3. Floating Point Errors in Trig

```python
# WRONG - Can produce NaN
angle = math.acos(dot / (mag1 * mag2))

# CORRECT - Clamp to valid range [-1, 1]
cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
angle = math.acos(cos_angle)
```

### 4. Forgetting Handler References

```python
# WRONG - Handler gets garbage collected
on_execute = CommandExecuteHandler()
cmd.execute.add(on_execute)

# CORRECT - Store reference
futil.add_handler(cmd.execute, command_execute)
```

### 5. Not Validating Dropdown Selection

```python
# WRONG - selectedItem can be None
name = dropdown.selectedItem.name

# CORRECT - Check first
if dropdown.selectedItem:
    name = dropdown.selectedItem.name
```

---

## Pre-commit Checklist

Before committing code, verify:

- [ ] `make validate` passes (check, lint, test)
- [ ] `make typecheck` passes
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No `Any` types without justification
- [ ] No bare `except:` without `futil.handle_error()`
- [ ] No magic numbers (use named constants)
- [ ] No hardcoded units (use `UnitConfig`)
- [ ] Handlers registered with `futil.add_handler()`
- [ ] New functionality has corresponding unit tests
- [ ] Edge cases tested (empty inputs, boundaries, invalid data)
- [ ] No console.log or debug code left in
- [ ] No commented-out code

---

## Key Algorithms

### Vector Cross Product Method

The rotation between bends is calculated as:

1. Each bend defines a plane containing the incoming and outgoing straight sections
2. The plane normal = cross_product(incoming_vector, outgoing_vector)
3. Rotation = angle between consecutive bend plane normals

This matches Bend-Tech and Rogue Fabrication methods.

### Path Ordering

User can select geometry in any order. The add-in:

1. Builds adjacency graph from endpoint connectivity
2. Finds path endpoints (elements with only 1 neighbor)
3. Traverses from one endpoint to the other
4. Validates alternating line-arc-line-arc pattern

---

## Questions?

If you're unsure about:
- **Type safety:** Default to stricter typing
- **SOLID principles:** Favor composition and small, focused classes
- **Testing:** Write defensive tests first, cover edge cases
- **Fusion API:** Check Text Commands window for errors

**When in doubt, ask before proceeding.**

---

**Remember: Code quality is not negotiable. This add-in calculates real-world bend rotations - errors mean wasted material and frustrated fabricators.**
