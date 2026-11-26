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
