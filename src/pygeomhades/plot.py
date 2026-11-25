from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def plot_profiles(
    profiles: dict, title: str = "", show: bool = False
) -> tuple[Figure, Axes]:
    """Plot the profiles of the volumes in the geometry using matplotlib.

    Parameters
    ----------
    profiles
        A dictionary mapping volume names to their profiles, where each profile
        is a dictionary with 3 fields `r`, `z` and `offset`.  The `r` and `z`
        fields are lists of the same length, containing the radius and z
        coordinates of the profile in mm, respectively. The `offset` field is
        the z position of the volume origin in mm, measured downwards from the
        top of the cryostat.
    title
        title of the plot.
    show
        if true, show the figure with :func:`matplotlib.pyplot.show`.
    """
    with plt.rc_context({"font.size": 14}):
        fig, ax = plt.subplots(figsize=(6, 8))

        for name, profile in profiles.items():
            ax.plot(
                profile["r"],
                [-(zt + profile["offset"]) for zt in profile["z"]],
                label=name,
            )

        ax.set_ylabel("height (mm)")
        ax.set_xlabel("radius (mm)")
        ax.set_aspect("equal")
        ax.set_title(title)
        ax.legend(fontsize=12)

    if show:
        plt.show()

    return fig, ax
