# Python vs GDML Geometry Implementation

As of the recent update, pygeomhades supports two methods for constructing geometry components:

1. **GDML-based**: The traditional method that reads GDML template files and performs string replacements
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

| Component | GDML Support | Python Support | Notes |
|-----------|--------------|----------------|-------|
| Wrap | ✓ | ✓ | Mylar wrap around detector |
| Cryostat | ✓ | ✓ | Aluminum alloy cryostat |
| Bottom Plate | ✓ | ✓ | Support plate with cavity |
| Th Plate | ✓ | ✓ | Thorium source plates |
| Holder (BEGe) | ✓ | ✓ | BEGe detector holder |
| Holder (ICPC) | ✓ | - | ICPC holder (GDML only) |
| Lead Castle (Table 1) | ✓ | ✓ | Lead shielding configuration |
| Lead Castle (Table 2) | ✓ | - | Alternative shielding (GDML only) |
| Source geometries | ✓ | - | Various source types (GDML only) |
| Source holders | ✓ | - | Source holder variants (GDML only) |

## Usage

All geometry creation functions accept a `from_gdml` parameter (default `True` for backward compatibility):

```python
from pygeomhades.create_volumes import create_wrap
from dbetto import AttrsDict

wrap_metadata = AttrsDict({
    "outer": {
        "height_in_mm": 100,
        "radius_in_mm": 50,
    },
    "inner": {
        "height_in_mm": 99,
        "radius_in_mm": 49,
    },
})

# Use GDML-based implementation (default)
wrap_lv = create_wrap(wrap_metadata, from_gdml=True)

# Use Python-based implementation
wrap_lv = create_wrap(wrap_metadata, from_gdml=False)
```

## Equivalence Testing

The package includes comprehensive tests to ensure that GDML and Python implementations produce equivalent geometries. These tests verify:

- Logical volume names match
- Materials are consistent
- Both methods produce valid pyg4ometry objects

See `tests/test_gdml_python_equivalence.py` for the full test suite.

## Limitations

Some complex geometries remain GDML-only for now:

- **ICPC holder**: Complex polycone geometry with many z-planes
- **Lead Castle Table 2**: Additional complexity not yet ported
- **Source geometries**: Multiple source types (Am, Ba, Co, Th) with specific geometries
- **Source holders**: Various holder configurations for different measurement positions

These can still be used via the GDML implementation (`from_gdml=True`).

## Future Work

The Python implementations can be extended to cover remaining components:

1. ICPC holder geometry
2. Lead castle table 2
3. Source geometries for all types
4. Source holder variants

Contributions are welcome!

## Implementation Details

The Python implementations use pyg4ometry primitives:

- **Materials**: Created using `geant4.Material` with element composition
- **Solids**: `Box`, `Tubs`, `GenericPolycone` for shapes
- **Boolean operations**: `Union`, `Subtraction` for complex shapes
- **Logical volumes**: `geant4.LogicalVolume` to combine solids and materials

Example of material creation:

```python
# Define aluminum alloy EN_AW-2011T8
al = geant4.ElementSimple("Aluminium", "Al", 13, 26.98)
cu = geant4.ElementSimple("Copper", "Cu", 29, 63.546)
pb = geant4.ElementSimple("Lead", "Pb", 82, 207.2)
bi = geant4.ElementSimple("Bismuth", "Bi", 83, 208.98)

en_aw_2011t8 = geant4.Material(
    name="EN_AW-2011T8", 
    density=2.84, 
    number_of_components=4, 
    registry=reg
)
en_aw_2011t8.add_element_massfraction(al, 0.932)
en_aw_2011t8.add_element_massfraction(cu, 0.06)
en_aw_2011t8.add_element_massfraction(pb, 0.004)
en_aw_2011t8.add_element_massfraction(bi, 0.004)
```

Example of polycone creation:

```python
# Create a polycone by tracing the outline
holder_solid = geant4.solid.GenericPolycone(
    "holder",
    0.0,  # start phi
    2.0 * np.pi,  # delta phi
    pR=[...],  # radii at each point
    pZ=[...],  # z positions at each point
    lunit="mm",
    aunit="rad",
    registry=reg,
)
```
