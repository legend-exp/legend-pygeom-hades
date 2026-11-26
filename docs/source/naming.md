# Naming conventions

Volume names follow the convention of the LEGEND-200
([docs](https://legend-pygeom-l200.readthedocs.io/en/stable/naming.html)) and
LEGEND-1000
([docs](https://legend-pygeom-l1000.readthedocs.io/en/stable/naming.html))
geometries. Regular expressions written for one geometry therefore also work on
the others.

- Volume names are snake_case and follow the scheme
  `[<group>_]<component>[_<material>][_<extra>]`. Example:
  `castle_bottom_plate_aluminium`. _remage_ can then select all volumes of one
  kind with a wildcard or regular expression, e.g. `source_.*` for all source
  parts or `.*_copper` for all copper parts.
  - Exception: the HPGe detector is named after the detector, e.g. `V07302A`.
- A solid, its logical volume and its physical volume share one name. Every
  logical volume is placed once.
  - Exception: the intermediate solids of a boolean chain (a solid built by
    adding or subtracting other solids) carry a suffix, e.g. `_step1` or
    `_base`. Only the final solid carries the name of the logical volume.

## Volumes

| name                            | material              | description                                                        |
| ------------------------------- | --------------------- | ------------------------------------------------------------------ |
| `world`                         | vacuum                | world volume                                                       |
| `lab_air`                       | air                   | laboratory, rotated by 180 deg so that its z axis points down      |
| `cryostat_wall_aluminium`       | aluminium alloy       | walls of the vacuum cryostat                                       |
| `cryostat_vacuum`               | vacuum                | inside of the cryostat                                             |
| _detector name_                 | germanium             | HPGe detector                                                      |
| `hpge_holder_aluminium`         | aluminium alloy       | detector holder                                                    |
| `hpge_wrap_hdpe`                | polyethylene (HDPE)   | detector wrap                                                      |
| `castle_lead`                   | lead                  | lead castle on the static tables                                   |
| `castle_plate_copper`           | copper                | copper plate between base and top block of the GERDA-era castle    |
| `castle_bottom_plate_aluminium` | aluminium             | plate on which the castle stands                                   |
| `source_active`                 | depends on the source | part of the source that holds the radioactive isotope              |
| `source_capsule_steel`          | steel                 | capsule of the Am-241 (HS1) and Th-228 sources                     |
| `source_capsule_pmma`           | PMMA (acrylic)        | capsule of the Am-241 (HS6) source                                 |
| `source_foil_hdpe`              | polyethylene (HDPE)   | foil that carries the Ba-133 and Co-60 sources                     |
| `source_ring_aluminium`         | aluminium             | ring around the foil of the Ba-133 and Co-60 sources               |
| `source_envelope_vacuum`        | vacuum                | volume that contains foil and ring of the Ba-133 and Co-60 sources |
| `source_epoxy`                  | epoxy                 | epoxy on the Th-228 source, inside the capsule                     |
| `source_collimator_copper`      | copper                | collimator of the Am-241 (HS1) source                              |
| `source_collimator_channel_air` | air                   | channel from the capsule to the surface of the collimator          |
| `source_holder_copper`          | copper                | copper holder of the Th-228 source                                 |
| `source_holder_bore_air`        | air                   | bore of the copper holder, which contains the capsule              |
| `source_holder_plate_lead`      | lead                  | lead plate that closes the bore of the copper holder (top only)    |
| `source_holder_pmma`            | PMMA (acrylic)        | source holder on top of or around the cryostat                     |

Which volumes exist depends on the measurement. For example, the castle volumes
exist only on the static tables, and the source volumes only if a source
position is given.
