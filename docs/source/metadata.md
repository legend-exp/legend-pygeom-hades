# Additional metadata

:::{important}

For using all its features, this package requires a working setup of
[`legend-metadata`](https://github.com/legend-exp/legend-metadata) and
[`hades-metadata`](https://github.com/legend-exp/hades-metadata) (_private
repositories_) before usage. A limited public geometry is also implemented.

:::

## HADES metadata

All dimensions of the test stand components are read from the `hardware/` folder
of `hades-metadata`. Lengths are in mm, and the `width` of round parts is their
diameter.

- `cryostat/<detector>`: for each detector, the dimensions of its vacuum
  cryostat (`cryostat`), of the detector holder (`holder`) and of the mylar wrap
  (`wrap`), and the positions of holder, wrap and detector in the cryostat. See
  the
  [vendor documents](https://legend-exp.atlassian.net/wiki/spaces/LEGEND/pages/397049975/Vendors+documents),
  `dimensions_holder_wrap.pdf` describes the names used for holder and wrap. The
  holder and wrap entries of a new detector can be created with
  [this tool](https://github.com/legend-exp/legend-g4simple-simulation/blob/master/tools/createICPCFiles.py).
- `setup/bottom_plate`: the aluminium plate between cryostat and lead castle.
- `setup/lead_castle/table1`, `setup/lead_castle/table2`: the lead castles of
  the two measurement tables. The table of a run is given by its FlashCam card
  interface (`daq_settings.flashcam.card_interface`): `efb1` for table 1, `efb2`
  for table 2.
- `sources/<source>`: the radioactive sources (e.g. `th_HS2`) with their
  capsules and collimators. `source_holder` names the source holder used in each
  measurement position (`top` or `lat`).
- `source_holders/<name>`: the acrylic source holders.

## Public dummy geometry

In the case the public geometry is used, this package contains **detector
metadata** files. These are based on our
[public testdata](https://github.com/legend-exp/legend-testdata/tree/main/data/legend/metadata/hardware/detectors/germanium/diodes),
slightly adjusted to fit our detector units. The package also ships copies of
the `setup`, `sources` and `source_holders` folders of `hades-metadata`, and
dummy cryostat, holder and wrap dimensions.

:::{warning}

In the case that the public geometry option is used, there may be overlaps
present with the wrap/holder. Use with caution...

:::
