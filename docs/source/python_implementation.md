# Python vs GDML Geometry Implementation

As of the recent update, pygeomhades supports two methods for constructing
geometry components:

1. **GDML-based**: The original method that reads GDML template files and
   performs string replacements
2. **Python-based**: A new direct implementation using pyg4ometry's Python API

## Motivation

The Python-based implementation offers several advantages:

- **Readability**: Python code is more readable than GDML XML
- **Maintainability**: Easier to understand and modify geometry definitions
- **Debugging**: Better error messages and easier to debug
- **Type checking**: Python code can be statically analyzed
- **No intermediate files**: Direct construction without temporary GDML files

## Available Components

The following components support both GDML and Python implementations:

| Component             | GDML Support | Python Support | Notes                              |
| --------------------- | ------------ | -------------- | ---------------------------------- |
| Wrap                  | ✓            | ✓              | Mylar wrap around detector         |
| Cryostat              | ✓            | ✓              | Aluminum alloy cryostat            |
| Bottom Plate          | ✓            | ✓              | Support plate with cavity          |
| Th Plate              | ✓            | ✓              | Thorium source plates              |
| Holder (BEGe)         | ✓            | ✓              | BEGe detector holder               |
| Holder (ICPC)         | ✓            | -              | ICPC holder (GDML only)            |
| Lead Castle (Table 1) | ✓            | ✓              | Lead shielding configuration       |
| Lead Castle (Table 2) | ✓            | -              | Alternative shielding (GDML only)  |
| Source geometries     | ✓            | -              | Various source types (GDML only)   |
| Source holders        | ✓            | -              | Source holder variants (GDML only) |

## Usage

All geometry creation functions accept a `from_gdml` parameter (default `True`
for backward compatibility):

```python
from pygeomhades.create_volumes import create_wrap
from dbetto import AttrsDict

wrap_metadata = AttrsDict(
    {
        "outer": {
            "height_in_mm": 100,
            "radius_in_mm": 50,
        },
        "inner": {
            "height_in_mm": 99,
            "radius_in_mm": 49,
        },
    }
)

# Use GDML-based implementation (default)
wrap_lv = create_wrap(wrap_metadata, from_gdml=True)

# Use Python-based implementation
wrap_lv = create_wrap(wrap_metadata, from_gdml=False)
```

:::{warning}

Some complex geometries remain GDML-only for now:

- **ICPC holder**: Complex polycone geometry with many z-planes
- **Lead Castle Table 2**: Additional complexity not yet ported
- **Source geometries**: Multiple source types (Am, Ba, Co, Th) with specific
  geometries
- **Source holders**: Various holder configurations for different measurement
  positions

These can still be used via the GDML implementation (`from_gdml=True`).

:::
