"""Colors of the volumes in the visualization.

Colors are RGBA lists (red, green, blue, opacity), each component between 0
and 1. They are stored in the ``pygeom_color_rgba`` attribute of each logical
volume, which :mod:`pygeomtools.viewer` reads. ``False`` hides the volume.
"""

from __future__ import annotations

import logging

from pyg4ometry import geant4

log = logging.getLogger(__name__)

#: Color of each material, by Geant4 material name. All germanium materials
#: (natural or enriched) share the ``Germanium`` entry.
MATERIAL_COLORS = {
    "Germanium": [0.45, 0.46, 0.48, 1.0],
    "metal_aluminium": [0.80, 0.81, 0.83, 1.0],
    "metal_aluminium_2011T8": [0.80, 0.81, 0.83, 1.0],
    "metal_steel_316Ti": [0.55, 0.56, 0.58, 1.0],
    "metal_copper": [0.72, 0.45, 0.20, 1.0],
    "metal_lead": [0.35, 0.36, 0.40, 1.0],
    "hdpe": [0.95, 0.95, 0.93, 0.8],  # white polyethylene
    "G4_MYLAR": [0.85, 0.75, 0.35, 0.8],  # gold-colored foil
    "pmma": [0.85, 0.92, 0.95, 0.5],
    "silica": [0.95, 0.95, 0.95, 0.5],
    "th_source_epoxy": [0.80, 0.60, 0.20, 0.7],
    "air": False,
    "G4_AIR": False,
    "vacuum": False,
    "G4_Galactic": False,
}

#: Opacity of volumes that enclose other parts of the setup, by logical volume
#: name. It replaces the opacity of the material, so that the inner parts stay
#: visible.
VOLUME_OPACITY = {
    "castle_lead": 0.05,
    "castle_bottom_plate_aluminium": 0.05,
    "cryostat_wall_aluminium": 0.5,
    "hpge_holder_aluminium": 0.8,
    "source_holder_copper": 0.5,
    "source_collimator_copper": 0.5,
}


def set_colors(registry: geant4.Registry) -> None:
    """Set the color of every logical volume in `registry` from its material.

    Materials without an entry in :data:`MATERIAL_COLORS` keep the default
    color of the viewer.
    """
    for lv in registry.logicalVolumeDict.values():
        material = lv.material.name
        if "Germanium" in material:
            material = "Germanium"

        if material not in MATERIAL_COLORS:
            log.warning("no color defined for material %s of %s", material, lv.name)
            continue

        color = MATERIAL_COLORS[material]
        if color is not False:
            color = [*color[:3], VOLUME_OPACITY.get(lv.name, color[3])]
        lv.pygeom_color_rgba = color
