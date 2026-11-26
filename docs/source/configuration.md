# Configuration

It is necessary to provide a configuration YAML file.

This should have a format similar to:

```yaml
detector: V13049A # the detector name
measurement: th_HS2_top_psa # the measurement name
daq_settings:
  flashcam:
    card_interface: efb1 # selects the table: efb1, efb2 (static) or efb3 (scanning)
source_position: # the source position, no source is built without it
  phi_in_deg: 0.0
  r_in_mm: 0.0
  z_in_mm: 38.0
```

The run configurations in `hardware/configuration` of `hades-metadata` have this
format (with additional fields) and can be used directly. Each of these files
holds all runs of one measurement, keyed by run name. On the command line,
select the run with `--run`:

```console
$ legend-pygeom-hades --run run0001 \
    --config hades-metadata/hardware/configuration/V07302A/c1/am_HS1_top_dlt.yaml \
    hades.gdml
```

:::{note}

The different measurements are described on
[[confluence]](https://legend-exp.atlassian.net/wiki/spaces/LEGEND/pages/1826750480/Analysis+of+characterization+data+WIP)
(note this is a private page).

:::

This metadata is stored on github
[[hades-metadata]](https://github.com/legend-exp/hades-metadata).

This metadata can then be passed directly to `pygeomhades` either on the command
line, on in python.

For example:

```python
db = dbetto.TextDB("hades-metadata")  # load the metadata

# construct the geometry
reg = pygeomhades.core.construct(
    db.hardware.configuration.V07302A.c1.am_HS1_top_dlt.run0001
)

# visualise
pygeomtools.viewer.visualize(reg)
```
