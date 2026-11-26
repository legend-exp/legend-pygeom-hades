"""Materials of the HADES setup."""

from __future__ import annotations

import pyg4ometry.geant4 as g4
from pygeomtools.materials import LegendMaterialRegistry, cached_property


class HadesMaterialRegistry(LegendMaterialRegistry):
    """The LEGEND materials, without optical properties, and the HADES-only ones."""

    def __init__(self, g4_registry: g4.Registry):
        super().__init__(g4_registry, enable_optical=False)

    @cached_property
    def th_source_epoxy(self) -> g4.Material:
        """Epoxy on the Th-228 source."""
        _th_source_epoxy = g4.Material(
            name="th_source_epoxy",
            density=1.129,
            number_of_components=4,
            registry=self.g4_registry,
        )
        for symbol, natoms in {"C": 41, "H": 49, "O": 7, "N": 3}.items():
            _th_source_epoxy.add_element_natoms(self.get_element(symbol), natoms=natoms)

        return _th_source_epoxy
