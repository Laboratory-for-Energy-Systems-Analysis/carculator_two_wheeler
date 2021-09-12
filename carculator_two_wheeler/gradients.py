import sys

import numpy as np

from . import DATA_DIR


def get_gradients(
    size=None,
):

    """Get driving cycle data as a Pandas `Series`.

    Driving cycles are given as km/h per second.
    Driving cycles for kick-scooters and bicycles are from
    http://brouter.de/brouter-web/#map=12/47.3195/8.5805/cyclosm&lonlats=8.404541,47.406508;8.580664,47.319341
    Driving cycles for scooters, mopeds and motorbikes are from the WMTC.

    There's no road gradients given for the WMTC.
    But we have some for the kick-scooters and bicycles' driving cycle.


    :returns: A pandas DataFrame object with driving time (in seconds) as index,
        and road gradients as values.
    :rtype: panda.Series

    """

    # definition of columns to select in the CSV file
    # each column corresponds to a size class
    # since the driving cycle is simulated for each size class

    size = (
        size
        if size is not None
        else [
            "Kick-scooter",
            "Bicycle <25",
            "Bicycle <45",
            "Bicycle cargo",
            "Moped <4kW",
            "Scooter <4kW",
            "Scooter 4-11kW",
            "Motorcycle 4-11kW",
            "Motorcycle 11-35kW",
            "Motorcycle >35kW",
        ]
    )

    dict_dc_sizes = {
        "Kick-scooter": 1,
        "Bicycle <25": 2,
        "Bicycle <45": 3,
        "Bicycle cargo": 4,
        "Moped <4kW": 5,
        "Scooter <4kW": 6,
        "Scooter 4-11kW": 7,
        "Motorcycle 4-11kW": 8,
        "Motorcycle 11-35kW": 9,
        "Motorcycle >35kW": 10,
    }

    try:
        list_col = [dict_dc_sizes[s] for s in size]
        arr = np.genfromtxt(DATA_DIR / "gradients.csv", delimiter=";")
        # we skip the headers
        dc = arr[1:, list_col]
        dc = dc[~np.isnan(dc)]
        return dc.reshape((-1, len(list_col)))

    except KeyError:
        print("The specified driving cycle could not be found.")
        sys.exit(1)
