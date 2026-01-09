# TubeBendCalculator

An Autodesk Fusion add-in for calculating multi-plane tube bend rotations and generating printable bend sheets from sketch geometry.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [AI Quick Start](#ai-quick-start-tubebendcalculator)
- [Usage](#usage)
- [Bend Sheet Output](#bend-sheet-output)
- [How Rotation is Calculated](#how-rotation-is-calculated)
- [Project Structure](#project-structure)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Overview

When bending tubes with multiple bends in different planes (roll cage tubes, exhaust systems, handrails), you need to know:

- **Rotation angles** between bends (how much to rotate the tube between each bend)
- **Mark positions** for where to align the tube on the bender die
- **Cut length** including any extra grip material

This add-in analyzes a sketch path of connected lines and arcs in Autodesk Fusion and calculates all of this automatically using the **vector cross product method**—the same approach used by Bend-Tech and Rogue Fabrication.

### Key Features

- **Rotation Calculation**: Calculates rotation angles between bend planes for multi-plane tube paths
- **Bend Sheet Generation**: Creates printable HTML bend sheets with step-by-step instructions
- **Bender Profile Management**: Save and manage tube bender configurations with multiple dies
- **Die Offset Support**: Accounts for die offset when calculating mark positions
- **Extra Grip Material**: Optionally add extra material at the start for bender grip
- **Unit Support**: Imperial (inches/fractions) and metric (mm) based on Fusion design settings
- **Per-Sketch Settings**: Saves tube OD, die selection, and precision with each sketch

## Installation

### From Source

1. Download or clone this repository
2. In Autodesk Fusion, go to **Tools > Add-Ins**
3. Click the **+** button next to "My Add-Ins"
4. Navigate to the `TubeBendCalculator` folder and select it
5. Check **Run on Startup** if you want the add-in to load automatically

### Verification

After installation, you should see a "Tube Bending" panel in the Tools tab with:
- **Create Bend Sheet** - Generate bend calculations from sketch geometry
- **Manage Benders** - Configure your bender and die profiles

## AI Quick Start: TubeBendCalculator

### When to Use This Add-in

- Bending tube/pipe with 2+ bends in different planes
- Need precise rotation angles between bends
- Building roll cages, exhaust systems, handrails, frames
- Using manual tube benders (JD2, Pro-Tools, etc.)

### Don't Use This Add-in When

- Single-plane bends only (all bends in same plane = 0° rotation)
- Using CNC tube benders with their own software
- Working with sheet metal bends (not tubular)

### Most Common Pattern (80% Case)

1. **Create sketch** with tube centerline as alternating lines and arcs:
   ```
   Line → Arc → Line → Arc → Line
   (straight → bend → straight → bend → straight)
   ```

2. **Select Create Bend Sheet** from Tools panel

3. **Select all geometry** (lines and arcs) in your path

4. **Configure**:
   - Tube OD: Your tube outer diameter
   - Bender/Die: Select matching CLR die
   - Extra Material: Add grip length if needed (typically 4-6")

5. **Generate** - Opens printable HTML bend sheet

### Critical Requirements

1. **Path must alternate line-arc-line-arc-line**
   - Cannot have two consecutive lines or two consecutive arcs
   - Each arc represents a bend, each line represents a straight section

2. **Geometry must be connected**
   - Arc endpoints must touch line endpoints
   - Small gaps cause calculation errors

3. **Arc radius = CLR (Center Line Radius)**
   - Draw arcs with the same radius as your bending die's CLR
   - Common CLRs: 4.5" for 1.5" tube, 5.5" for 1.75" tube

4. **Die offset matters**
   - Measure from die edge to bend tangent point
   - Typical range: 0.5" - 1.0"

### Common Mistakes to Avoid

- **Wrong**: Drawing bends as polylines or splines (must use sketch arcs)
- **Wrong**: Mismatched arc radius and die CLR (causes calculation errors)
- **Wrong**: Forgetting die offset (mark positions will be wrong)
- **Wrong**: Not adding grip material when your bender needs it

### Integration Notes

- Uses Fusion document attributes to persist settings per-sketch
- Bender profiles stored in `resources/benders.json`
- Respects design unit settings (in/mm) automatically

## Usage

### Creating a Bend Sheet

1. **Create a sketch** with your tube centerline path:
   - Use **lines** for straight sections
   - Use **arcs** for bends (arc radius = CLR)
   - Path must alternate: line → arc → line → arc → line

2. **Launch the command**: Tools > Tube Bending > Create Bend Sheet

3. **Select geometry**: Click all lines and arcs in your path

4. **Configure options**:
   | Option | Description |
   |--------|-------------|
   | Tube OD | Outside diameter of your tube |
   | Bender | Select your bender profile |
   | Die | Select die (sets CLR and offset) |
   | Precision | Display precision (1/16", 1/32", 1mm, etc.) |
   | Extra Material | Grip material at tube start |

5. **Click OK** to generate the bend sheet (opens in browser)

### Managing Benders

Use **Manage Benders** to configure your equipment:

**Bender Settings:**
- Name: Display name (e.g., "JD2 Model 3")
- Min Grip: Minimum grip length required

**Die Settings:**
- Name: Die identifier (e.g., "1.75\" x 5.5\" CLR")
- Tube OD: Tube outer diameter this die accepts
- CLR: Center line radius of the bend
- Offset: Distance from die edge to bend tangent point

## Bend Sheet Output

The generated HTML bend sheet includes:

### Cut Length
Total tube length to cut, including extra grip material.

### Bend Data Table
| Step | Segment | Length | Starts At | Ends At | Bend Angle | Rotation Before |
|------|---------|--------|-----------|---------|------------|-----------------|
| 1 | Straight 1 | 12" | 0" | 12" | — | — |
| 2 | BEND 1 | 4.32" | 12" | 16.32" | 45.0° | — |
| 3 | Straight 2 | 8" | 16.32" | 24.32" | — | **30.0°** |
| ... | ... | ... | ... | ... | ... | ... |

### Bender Setup
Mark positions aligned to die end with rotation instructions.

### Step-by-Step Procedure
1. Cut tube to [total length]
2. Mark at [position] from start
3. Rotate tube [angle]
4. Align mark to die end, bend [angle]
5. (Repeat for each bend)

## How Rotation is Calculated

Each bend defines a **plane** containing the incoming and outgoing straight sections:

1. **Calculate bend plane normal** for each bend:
   ```
   normal = cross_product(incoming_vector, outgoing_vector)
   ```

2. **Calculate rotation** between consecutive bends:
   ```
   rotation = angle_between(previous_normal, current_normal)
   ```

This is the **vector cross product method**—the industry-standard approach used by Bend-Tech, Rogue Fabrication, and professional tube bending software.

### Example

For a tube with two bends:
- Bend 1: 45° in the XY plane
- Bend 2: 30° rotated 60° from Bend 1's plane

The rotation before Bend 2 would be **60°**—you rotate the tube 60° in the bender before making the second bend.

## Project Structure

```
TubeBendCalculator/
├── TubeBendCalculator.py      # Entry point (run/stop)
├── TubeBendCalculator.manifest # Add-in metadata
├── config.py                  # Global configuration
├── Makefile                   # Development tasks
├── commands/                  # UI command handlers
│   ├── createBendSheet/       # Bend sheet generation command
│   └── manageBenders/         # Bender profile management
├── core/                      # Pure calculation logic (no Fusion deps)
│   ├── calculations.py        # Bend/rotation calculations
│   ├── formatting.py          # Length/angle formatting
│   ├── geometry.py            # Vector math utilities
│   ├── geometry_extraction.py # Extract geometry from Fusion
│   ├── html_generator.py      # Bend sheet HTML generation
│   ├── path_analysis.py       # Path connectivity analysis
│   └── path_ordering.py       # Order geometry into path
├── models/                    # Data structures
│   ├── bender.py              # Bender/Die dataclasses
│   ├── bend_data.py           # Bend calculation results
│   ├── types.py               # Type aliases
│   └── units.py               # Unit configuration
├── storage/                   # Persistence
│   ├── attributes.py          # Fusion document attributes
│   └── profiles.py            # JSON bender profiles
├── tests/                     # Unit tests (pytest)
├── lib/fusionAddInUtils/      # Handler management utilities
├── resources/                 # Runtime resources
│   └── benders.json           # Saved bender profiles
└── typings/                   # Type stubs for Fusion API
```

### Layer Architecture

| Layer | Fusion API | Unit Testable |
|-------|------------|---------------|
| `commands/` | Heavy | No |
| `core/` | None | Yes |
| `models/` | None | Yes |
| `storage/profiles.py` | None | Yes |
| `storage/attributes.py` | Yes | No |

The `core/` and `models/` layers are intentionally kept free of Fusion API dependencies to enable thorough unit testing.

## Development

### Prerequisites

- Python 3.10+
- pytest (testing)
- ruff (linting)
- pyright (type checking)

### Quick Start

```bash
# Run all validation (recommended before commits)
make validate

# Individual checks
make check      # Syntax check
make lint       # Linting
make typecheck  # Type checking
make test       # Unit tests
```

### Running Tests

```bash
# Basic test run
make test

# With verbose output
PYTHONPATH="$PWD" pytest tests/ -v

# With coverage
PYTHONPATH="$PWD" pipx run --spec pytest-cov pytest --cov=core --cov=models --cov=storage
```

**Current coverage**: 82% on testable modules (`core/`, `models/`, `storage/`).

### Code Standards

This project enforces strict standards (see `CLAUDE.md` for full details):

- **Type hints required** on all functions
- **No `Any` types** without justification
- **SOLID principles** throughout
- **Defensive testing** for edge cases

### Type Checking

```bash
make typecheck
# or
pyright --project pyrightconfig.json
```

Zero errors required on `core/`, `models/`, and `storage/`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make validate` (must pass)
5. Submit a pull request

### Contribution Guidelines

- All functions must have type hints
- All public functions must have docstrings
- New functionality requires corresponding unit tests
- Edge cases must be tested (empty inputs, boundaries, invalid data)
- No bare `except:` without error handling

## Requirements

- **Autodesk Fusion** (Windows or macOS)
- No external Python dependencies (self-contained)

## License

MIT License - See LICENSE file for details.

## Acknowledgments

The rotation calculation method is based on the vector cross product approach documented by:
- Bend-Tech
- Rogue Fabrication
- Various tube bending technical resources