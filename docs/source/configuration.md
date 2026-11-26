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
format (with additional fields) and can be used directly. They are stored as
`<detector>/<campaign>/<measurement>.yaml`, and each file holds all runs of one
measurement, keyed by run name. On the command line, select a run by these keys:

```console
$ legend-pygeom-hades --detector V07302A --campaign c1 \
    --measurement am_HS1_top_dlt --run run0001 hades.gdml
```

A key can be left out if it has only one choice. Otherwise the program stops and
lists the available choices, so leaving out keys also shows what is in the
metadata. This lookup reads the private `hades-metadata` and does not work with
`--public-geom`.

A run configuration file can also be given directly with `--config`. For a file
with several runs, select one with `--run`:

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

## Selecting a run with `run_key`

A configuration can name a run of `hades-metadata` with the `run_key` field,
instead of giving the run fields. The format is
`<detector>-<campaign>-<measurement>-<run>`:

```yaml
run_key: V07302A-c1-am_HS1_top_dlt-run0001
```

The geometry is then built from the configuration of that run. The other
top-level fields of the configuration replace the fields of the run, e.g. to
move the source in a systematic study:

```yaml
run_key: V07302A-c1-am_HS1_top_dlt-run0001
source_position: # replaces the whole source_position of the run
  phi_in_deg: 0.0
  r_in_mm: 46.0
  z_in_mm: 5.0
```

Such a file is given with `--config`, or its fields are passed to
`pygeomhades.core.construct` in Python. Like the lookup on the command line,
`run_key` reads the private `hades-metadata` and does not work with the public
geometry.
