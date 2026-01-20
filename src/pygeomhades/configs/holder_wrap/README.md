# Holder and wrap dimensions

In this repository, you can find the json files related to the dimensions of the
holder and wrap of each ICPC detector. See documentation
[here](https://legend-exp.atlassian.net/wiki/spaces/LEGEND/pages/397049975/Vendors+documents).
The <code>dimensions_holder_wrap.pdf</code> describes the names used in the json
files.

If you need to create a json file for a new detector, you can even use the tool
in
<code>/lfs/l1/legend/detector_char/enr/hades/simulations/legend-g4simple-simulation/legend/tools</code>.
There, <code>createFiles.py</code> contains a useful function for this purpose.

```console
  $ python3
  >>> import createFiles.py as cF
  >>> cf.createJSONFile("DetectorNameYouNeed")
```

Follow the instructions. In <code>holder_wrap</code> repository, it would create
a new json file of the dimensions of the holder and wrap with the same structure
of the other json files already existing.
