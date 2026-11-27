# Description of the geometry

The geometry of the HADES test stand consists of the HPGe detector in a vacuum
cryostat, with various possible sources and an outer lead shield (in some
measurements).

During detector characterisation a very large number of measurements are
performed. This package allows to easily generate the geometry for any
measurement and run (see {doc}`configuration`).

A more detailed description can be found in
[[link]](https://www.research.unipd.it/retrieve/aaa7ce91-013d-4975-8827-c0eff2fb37af/Thesis_Valentina_Biancacci.pdf).

## Physical volumes

- The HPGe detector physical volume is the name of the detector.
- The part of the source that holds the radioactive isotope is named
  `source_active`.

::: {tip}

In _remage_ the physical volume `source_active` should usually be set as the
volume for vertex confinement to simulate the calibration source.

:::

All volume names are listed in {doc}`naming`.

## Volume hierarchy

A volume that is entirely inside another one is placed in it (as a daughter
volume). Volumes that sit next to each other are placed in the same mother
volume:

```
world
└── lab_air
    ├── cryostat_wall_aluminium        full cylinder
    │   └── cryostat_vacuum            the cryostat walls are the aluminium around it
    │       ├── hpge_holder_aluminium
    │       ├── hpge_wrap_hdpe
    │       ├── hpge_foil_mylar            BEGe cryostats only
    │       └── <detector name>
    ├── source_holder_pmma, source parts (each source with its own daughters)
    ├── castle_bottom_plate_aluminium
    ├── castle_lead
    └── castle_plate_copper            GERDA-era castle only
```

Parts that touch in the real setup (e.g. the lead castle standing on the bottom
plate, or the wrap resting on the crystal) are separated by a gap of 1 µm, and a
daughter volume is kept 1 µm away from the surface of its mother. Geant4 cannot
tell on which side of a shared surface a point is, and the gap is far too small
to change the simulated physics.
