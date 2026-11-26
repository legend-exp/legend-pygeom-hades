from __future__ import annotations

import argparse
import logging

from dbetto import AttrsDict, utils
from legendmeta import HadesMetadata
from pyg4ometry import config as meshconfig
from pygeomtools import geometry, write_pygeom

from . import _version, core
from .metadata import _choose, select_run

log = logging.getLogger(__name__)


def dump_gdml_cli(argv: list[str] | None = None) -> None:
    args = _parse_cli_args(argv)

    logging.basicConfig()
    if args.verbose:
        logging.getLogger("pygeomhades").setLevel(logging.DEBUG)
    if args.debug:
        logging.root.setLevel(logging.DEBUG)

    vis_scene = {}
    if isinstance(args.visualize, str):
        vis_scene = utils.load_dict(args.visualize)

    if args.clip_geometry:
        vis_scene["clipper"] = [
            {"origin": [0, 0, 0], "normal": [1, 0, 0], "close_cuts": False}
        ]

    if (args.visualize and vis_scene.get("fine_mesh", True)) or args.check_overlaps:
        meshconfig.setGlobalMeshSliceAndStack(100)

    registry = core.construct(
        _select_config(args),
        public_geometry=args.public_geom,
        plot_profiles=args.plot_profile,
    )

    if args.print_volumes:
        geometry.print_volumes(registry, args.print_volumes)

    if args.check_overlaps:
        msg = "checking for overlaps"
        log.info(msg)
        registry.worldVolume.checkOverlaps(recursive=True)

    # commit auxvals, and write to GDML file if requested.
    if args.filename is not None:
        log.info("exporting GDML geometry to %s", args.filename)
    write_pygeom(registry, args.filename)

    if args.visualize:
        log.info("visualizing...")
        from pygeomtools import viewer

        viewer.visualize(registry, vis_scene)


def _select_config(args: argparse.Namespace) -> AttrsDict:
    """Return the configuration of the run selected on the command line."""
    if args.config is not None:
        config = AttrsDict(utils.load_dict(args.config))
        if args.run is None and ("detector" in config or "run_key" in config):
            return config
        return config[_choose(config, "run", args.run)]

    return select_run(
        HadesMetadata(lazy=True).__path__,
        args.detector,
        args.campaign,
        args.measurement,
        args.run,
    )


def _parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="legend-pygeom-hades",
        description="%(prog)s command line interface",
    )

    # global options
    parser.add_argument(
        "--version",
        action="version",
        help="""Print %(prog)s version and exit""",
        version=_version.__version__,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="""Increase the program verbosity""",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="""Increase the program verbosity to maximum""",
    )
    parser.add_argument(
        "--visualize",
        "-V",
        nargs="?",
        const=True,
        help="""Open a VTK visualization of the generated geometry (with optional scene file)""",
    )
    parser.add_argument(
        "--plot-profile",
        "-p",
        action="store_true",
        help="""Plot the profiles of the volumes inside the cryostat.""",
    )
    parser.add_argument(
        "--clip-geometry",
        action="store_true",
        help="""Clip the geometry for visualization purposes""",
    )
    parser.add_argument(
        "--check-overlaps",
        action="store_true",
        help="""Check for overlaps with pyg4ometry (note: this might not be accurate)""",
    )
    parser.add_argument(
        "--print-volumes",
        action="store",
        choices=("logical", "physical", "detector"),
        help="""Print a list of logical or physical volume names (from the pyg4ometry registry)""",
    )

    geom_opts = parser.add_argument_group("geometry options")
    geom_opts.add_argument(
        "--public-geom",
        action="store_true",
        default=None,
        help="""Create a geometry from public testdata only.""",
    )

    source = geom_opts.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--config",
        help="""Path to a run configuration file (one run, a run_key, or several
        runs keyed by name).""",
    )
    source.add_argument(
        "--detector",
        help="""Detector name. Selects the run configuration from hades-metadata
        (hardware/configuration).""",
    )
    geom_opts.add_argument(
        "--campaign",
        help="""Campaign (e.g. c1). Optional if the detector has only one.""",
    )
    geom_opts.add_argument(
        "--measurement",
        help="""Measurement name (e.g. am_HS1_top_dlt). Optional if there is only
        one.""",
    )
    geom_opts.add_argument(
        "--run",
        help="""Run name (e.g. run0002). Optional if there is only one.""",
    )

    parser.add_argument(
        "filename",
        default=None,
        nargs="?",
        help="""File name for the output GDML geometry.""",
    )

    args = parser.parse_args(argv)

    if args.filename is None and not (
        args.visualize or args.plot_profile or args.print_volumes or args.check_overlaps
    ):
        parser.error("no output file, visualization or other action specified")

    if args.config is not None and (args.campaign or args.measurement):
        parser.error("--campaign and --measurement need --detector, not --config")
    if args.detector is not None and args.public_geom:
        parser.error(
            "--detector needs the private hades-metadata, use --config with --public-geom"
        )

    return args
