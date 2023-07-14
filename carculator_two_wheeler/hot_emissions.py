import numpy as np
import pandas as pd
import xarray as xr

from . import DATA_DIR


def _(o):
    """Add a trailing dimension to make input arrays broadcast correctly"""
    if isinstance(o, (np.ndarray, xr.DataArray)):
        return np.expand_dims(o, -1)
    else:
        return o


def get_hot_emission_factors():
    """Hot emissions factors extracted for trucks from HBEFA 4.1
    detailed by size, powertrain and EURO class for each substance.
    """
    fp = DATA_DIR / "hot_emissions.csv"

    hot = pd.read_csv(fp, sep=";")

    return hot.groupby(["euro_class", "component", "size"]).sum()["value"].to_xarray()


class HotEmissionsModel:
    """
    Calculate hot pollutants emissions based on HBEFA 4.1 data, function of fuel consumption
    for vehicles with a combustion engine.

    :param cycle: Driving cycle. Pandas Series of second-by-second speeds (km/h) or name (str)
        of cycle e.g., "WLTC","WLTC 3.1","WLTC 3.2","WLTC 3.3","WLTC 3.4","CADC Urban","CADC Road",
        "CADC Motorway","CADC Motorway 130","CADC","NEDC".
    :type cycle: pandas.Series

    """

    def __init__(self, cycle):
        self.cycle = cycle

        self.hot = get_hot_emission_factors()

    def get_hot_emissions(self, powertrain_type, euro_class, sizes, energy_consumption):
        """
        Calculate hot pollutants emissions given a powertrain type (i.e., ICEV-p) and a EURO pollution class, per air sub-compartment
        (i.e., urban, suburban and rural).

        Emission factors are from:
        https://www.eea.europa.eu/publications/emep-eea-guidebook-2019/part-b-sectoral-guidance-chapters/1-energy/1-a-combustion/road-transport-appendix-4-emission/view

        Originally, the sizes are given as:

        * Mopeds 2-stroke <50 cm³
        * Mopeds 4-stroke <50 cm³
        * Motorcycles 4-stroke <250 cm³
        * Motorcycles 4-stroke 250 - 750 cm³
        * Motorcycles 4-stroke >750 cm³

        and we map them to:

        * Moped <4kW
        * Scooter <4kW
        * Scooter 4-11kW and Motorcycle 4-11kW
        * Motorcycle 11-35kW
        * Motorcycle >35kW

        The emission sums are further divided into `air compartments`: urban, suburban and rural.

        :param powertrain_type: "ICEV-p"
        :type powertrain_type: str
        :param euro_class: integer, corresponding to the EURO pollution class
        :type euro_class: float
        :param energy_consumption: tank-to-wheel energy consumption for each second of the driving cycle
        :type energy_consumption: xarray
        :param yearly_km: annual mileage, to calculate cold start emissions
        :return: Pollutants emission per km driven, per air compartment.
        :rtype: numpy.array
        """

        # Check if the powertrains passed are valid
        if set(powertrain_type).intersection({"BEV"}):
            raise TypeError("Wrong powertrain!")

        hot_emissions = self.hot.sel(
            euro_class=euro_class,
            size=sizes,
            component=[
                "CO",
                "NOx",
                "VOC",
                "PM2.5",
                "CH4",
                "NH3",
                "N2O",
                "Ethane",
                "Propane",
                "Butane",
                "Pentane",
                "Hexane",
                "Cyclohexane",
                "Heptane",
                "Ethene",
                "Propene",
                "1-Pentene",
                "Toluene",
                "m-Xylene",
                "o-Xylene",
                "Formaldehyde",
                "Acetaldehyde",
                "Benzaldehyde",
                "Acetone",
                "Methyl ethyl ketone",
                "Acrolein",
                "Styrene",
                "PAHs",
                "Arsenic",
                "Selenium",
                "Zinc",
                "Copper",
                "Nickel",
                "Chromium",
                "Chromium VI",
                "Mercury",
                "Cadmium",
                "Benzene",
            ],
        ).transpose("component", "euro_class", "size")

        distance = self.cycle.sum() / 3600

        # Emissions for each second of the driving cycle equal:
        # a * energy consumption
        # with a being a coefficient given by fitting EEA/EMEP data

        # energy consumption is given in kj for each second
        # emissions are in grams per MJ

        hot = (
            (
                hot_emissions.values[..., None, None].transpose(0, 2, 1, 3, 4)
                * energy_consumption.values
            )
            / 1000
            / 1000
        )

        # we split the emission per air compartment
        # as we know how the WMTC driving cycle distributes

        urban = hot[..., :600].sum(axis=-1) / distance
        suburban = hot[..., 601:1200].sum(axis=-1) / distance
        rural = hot[..., 1200:].sum(axis=-1) / distance

        return np.vstack((urban, suburban, rural)).transpose(1, 0, 2, 3)
