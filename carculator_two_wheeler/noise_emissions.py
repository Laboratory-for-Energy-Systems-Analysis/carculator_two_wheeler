import numexpr as ne
import numpy as np

from . import get_standard_driving_cycle


class NoiseEmissionsModel:
    """
    Calculate propulsion noise emissions for combustion and electric vehicles, based on CNOSSOS model.
    For two-wheelers, there is not rolling noise emissions.

    :param cycle: Driving cycle. Pandas Series of second-by-second speeds (km/h).
    :type cycle: pandas.Series

    """

    def __init__(self, sizes):

        self.sizes = sizes
        self.cycle = get_standard_driving_cycle(size=sizes)

    def propulsion_noise(self, powertrain_type):
        """Calculate noise from propulsion engine and gearbox.
        Model from CNOSSOS-EU project
        (http://publications.jrc.ec.europa.eu/repository/bitstream/JRC72550/cnossos-eu%20jrc%20reference%20report_final_on%20line%20version_10%20august%202012.pdf)

        For electric cars, special coefficients are applied from
        (`Pallas et al. 2016 <https://www.sciencedirect.com/science/article/pii/S0003682X16301608>`_ )

        Also, for electric cars, a warning signal of 56 dB is added when the car drives at 20 km/h or lower.

        :returns: A numpy array with propulsion noise (dB) for all 8 octaves, per second of driving cycle
        :rtype: numpy.array

        """
        cycle = np.array(self.cycle)

        # Noise sources are calculated for speeds above 20 km/h.
        if powertrain_type in ("combustion", "electric"):
            array = np.tile((cycle - 70) / 70, 8).reshape((8, cycle.shape[-1], -1))
            constants_scooter = np.array(
                (88, 87.5, 89.5, 93.7, 96.6, 98.8, 93.9, 88.7)
            ).reshape((-1, 1))
            constants_motorcycle = np.array(
                (95, 97.2, 92.7, 92.9, 94.7, 93.2, 90.1, 86.5)
            ).reshape((-1, 1))
            coefficients_scooter = np.array(
                (4.2, 7.4, 9.8, 11.6, 15.7, 18.9, 20.3, 20.6)
            ).reshape((-1, 1))
            coefficients_motorcycle = np.array(
                (3.2, 5.9, 11.9, 11.6, 11.5, 12.6, 11.1, 12)
            ).reshape((-1, 1))

            for x in range(0, cycle.shape[-1]):
                if self.sizes[x] in ["Moped <4kW", "Scooter <4kW"]:
                    array[:, x] = array[:, x] * coefficients_scooter + constants_scooter
                else:
                    array[:, x] = (
                        array[:, x] * coefficients_motorcycle + constants_motorcycle
                    )

            if powertrain_type == "electric":
                # For electric cars, we add correction factors
                # We also add a 56 dB loud sound signal when the speed is below 20 km/h.

                correction = np.array((0, 1.7, 4.2, 15, 15, 15, 13.8, 0)).reshape(
                    (-1, 1, 1)
                )
                array -= correction

        return array

    def get_sound_power_per_compartment(self, powertrain_type):
        """
        Calculate sound energy (in J/s) over the driving cycle duration from sound power (in dB).
        The sound energy sums are further divided into `geographical compartments`: urban, suburban and rural.

        * *urban*: from 0 to 50 km/k
        * *suburban*: from 51 km/h to 80 km/h
        * *rural*: above 80 km/h

        :return: Sound energy (in Joules) per km driven, per geographical compartment.
        :rtype: numpy.array
        """

        if powertrain_type not in ("combustion", "electric"):
            raise TypeError("The powertrain type is not valid.")

        # propulsion noise, in dB, for each second of the driving cycle
        propulsion = self.propulsion_noise(powertrain_type)

        # convert dBs to Watts (or J/s)
        sound_power = ne.evaluate("(10 ** -12) * (10 ** (propulsion / 10))")

        # we split the emission per air compartment
        # as we know how the WMTC driving cycle distributes

        distance = self.cycle.sum() / 3600
        urban = sound_power[..., :600].sum(axis=-1) / distance
        suburban = sound_power[..., 601:1200].sum(axis=-1) / distance
        rural = sound_power[..., 1200:].sum(axis=-1) / distance

        return np.vstack((urban, suburban, rural))
