# AI Agents

This repo implements the geometry of the HADES HPGe characterization setup, used
for Geant4 Monte Carlo simulations. This setup is used to characterize detectors
for the LEGEND experiment. The implementation is based on the Python package
`pyg4ometry`

## Metadata

Geometry generation is largely based on metadata, stored at
https://github.com/legend-exp/hades-metadata. The metadata can be accessed with
a dedicated Python class (`HadesMetadata`) provided by the `pylegendmeta`
package.

The metadata repository contains a lot of information about the geometry. It is
extensively documented with `README.md` files --- refer to them.

Important to know that the files in `hades-metadata/hardware/configuration` come
straight from the DAQ system in HADES (source code available
[here](https://github.com/legend-exp/hades-l200tests-daq). Their format is fixed
and can't be changed.

The metadata is also accessed by the
[HADES data processing pipeline](https://github.com/legend-exp/hades-dataflow).
