import numpy as np
import pandas as pd
import stats_arrays as sa
import xarray as xr

from .two_wheelers_input_parameters import TwoWheelerInputParameters as tw_i_p


def fill_xarray_from_input_parameters(twip, sensitivity=False, scope=None):
    """Create an `xarray` labeled array from the sampled input parameters.


    This function extracts the parameters' names and values contained in the `parameters` attribute of the
    :class:`CarInputParameters` class in :mod:`car_input_parameters` and insert them into a multidimensional
    numpy-like array from the *xarray* package (http://xarray.pydata.org/en/stable/).

    Returns:

    * tuple (`size_dict`, `powertrain_dict`, `parameter_dict`, `year_dict`)
    * array
       * Dimensions of `array`:
            0. Vehicle size (str), e.g. "small", "medium"
            1. Powertrain (str), e.g. "ICE-p", "BEV"
            2. Year (int)
            3. Samples


    :param sensitivity: boolean value
    :param twip: instance of the :class:`CarInputParameters` class in :mod:`car_input_parameters`.
    :param scope: a dictionary to narrow down the scope of vehicles to consider
    :returns: `tuple`, `xarray.DataArray`
    """

    # Check whether the argument passed is a twip object
    if not isinstance(twip, tw_i_p):
        raise TypeError(
            "The argument passed is not an object of the TwoWheelersInputParameter class"
        )

    if scope is None:
        scope = {"size": twip.sizes, "powertrain": twip.powertrains, "year": twip.years}
    else:
        if "size" not in scope:
            scope["size"] = twip.sizes
        if "powertrain" not in scope:
            scope["powertrain"] = twip.powertrains
        if "year" not in scope:
            scope["year"] = twip.years

    if any(s for s in scope["size"] if s not in twip.sizes):
        raise ValueError("One of the size types is not valid.")

    if any(y for y in scope["year"] if y not in twip.years):
        raise ValueError("One of the years defined is not valid.")

    if any(pt for pt in scope["powertrain"] if pt not in twip.powertrains):
        raise ValueError("One of the powertrain types is not valid.")

    if not sensitivity:
        array = xr.DataArray(
            np.zeros(
                (
                    len(scope["size"]),
                    len(scope["powertrain"]),
                    len(twip.parameters),
                    len(scope["year"]),
                    twip.iterations or 1,
                )
            ),
            coords=[
                scope["size"],
                scope["powertrain"],
                twip.parameters,
                scope["year"],
                np.arange(twip.iterations or 1),
            ],
            dims=["size", "powertrain", "parameter", "year", "value"],
        )
    else:
        params = ["reference"]
        params.extend([a for a in twip.input_parameters])
        array = xr.DataArray(
            np.zeros(
                (
                    len(scope["size"]),
                    len(scope["powertrain"]),
                    len(twip.parameters),
                    len(scope["year"]),
                    len(params),
                )
            ),
            coords=[twip.sizes, twip.powertrains, twip.parameters, twip.years, params],
            dims=["size", "powertrain", "parameter", "year", "value"],
        )

    size_dict = {k: i for i, k in enumerate(scope["size"])}
    powertrain_dict = {k: i for i, k in enumerate(scope["powertrain"])}
    year_dict = {k: i for i, k in enumerate(scope["year"])}
    parameter_dict = {k: i for i, k in enumerate(twip.parameters)}

    if not sensitivity:
        for param in twip:
            pwt = (
                set(twip.metadata[param]["powertrain"])
                if isinstance(twip.metadata[param]["powertrain"], list)
                else {twip.metadata[param]["powertrain"]}
            )

            size = (
                set(twip.metadata[param]["sizes"])
                if isinstance(twip.metadata[param]["sizes"], list)
                else {twip.metadata[param]["sizes"]}
            )

            year = (
                set(twip.metadata[param]["year"])
                if isinstance(twip.metadata[param]["year"], list)
                else {twip.metadata[param]["year"]}
            )

            if (
                pwt.intersection(scope["powertrain"])
                and size.intersection(scope["size"])
                and year.intersection(scope["year"])
            ):
                array.loc[
                    dict(
                        powertrain=[p for p in pwt if p in scope["powertrain"]],
                        size=[s for s in size if s in scope["size"]],
                        year=[y for y in year if y in scope["year"]],
                        parameter=twip.metadata[param]["name"],
                    )
                ] = twip.values[param]
    else:
        for param in twip.input_parameters:
            names = [n for n in twip.metadata if twip.metadata[n]["name"] == param]

            for name in names:
                pwt = (
                    set(twip.metadata[name]["powertrain"])
                    if isinstance(twip.metadata[name]["powertrain"], list)
                    else {twip.metadata[name]["powertrain"]}
                )

                size = (
                    set(twip.metadata[name]["sizes"])
                    if isinstance(twip.metadata[name]["sizes"], list)
                    else {twip.metadata[name]["sizes"]}
                )

                year = (
                    set(twip.metadata[name]["year"])
                    if isinstance(twip.metadata[name]["year"], list)
                    else {twip.metadata[name]["year"]}
                )

                vals = [
                    twip.values[name] for _ in range(0, len(twip.input_parameters) + 1)
                ]
                vals[twip.input_parameters.index(param) + 1] *= 1.1

                array.loc[
                    dict(
                        powertrain=[p for p in pwt if p in scope["powertrain"]],
                        size=[s for s in size if s in scope["size"]],
                        year=[y for y in year if y in scope["year"]],
                        parameter=twip.metadata[name]["name"],
                    )
                ] = vals

    return (size_dict, powertrain_dict, parameter_dict, year_dict), array


def modify_xarray_from_custom_parameters(fp, array):
    """
    Override default parameters values in `xarray` based on values provided by the user.

    This function allows to override one or several default parameter values by providing either:

    * a file path to an Excel workbook that contains the new values
    * or a dictionary

    The dictionary must be of the following format:

    .. code-block:: python

        {
            (parameter category,
                powertrain,
                size,
                parameter name,
                uncertainty type): {
                                    (year, 'loc'): value,
                                    (year, 'scale'): value,
                                    (year, 'shape'): value,
                                    (year, 'minimum'): value,
                                    (year, 'maximum'): value
            }

        }

    For example:

    .. code-block:: python

        {
            ('Driving',
            'all',
            'all',
            'lifetime kilometers',
            'none'): {
                (2018, 'loc'): 150000, (2040, 'loc'): 150000
                }

        }

    :param array:
    :param fp: File path of workbook with new values or dictionary.
    :type fp: str or dict

    """

    if isinstance(fp, str):
        try:
            d = pd.read_excel(
                fp,
                header=[0, 1],
                index_col=[0, 1, 2, 3, 4],
                sheet_name="Custom_parameters",
            ).to_dict(orient="index")
        except:
            raise FileNotFoundError("Custom parameters file not found.")
    elif isinstance(fp, dict):
        d = fp
    else:
        raise TypeError("The format passed as parameter is not valid.")

    FORBIDDEN_KEYS = ["Driving cycle", "Background", "Functional unit"]

    for k in d:
        if k[0] not in FORBIDDEN_KEYS:
            if not isinstance(k[1], str):
                pt = [p.strip() for p in k[1] if p]
                pt = [p for p in pt if p]
                pt = list(pt)
            elif k[1] == "all":
                pt = array.coords["powertrain"].values
            else:
                if k[1] in array.coords["powertrain"].values:
                    pt = [k[1]]
                elif all(
                    p
                    for p in k[1].split(", ")
                    if p in array.coords["powertrain"].values
                ):
                    pt = [p for p in k[1].split(", ")]
                else:
                    print(
                        "{} is not a recognized powertrain. It will be skipped.".format(
                            k[1]
                        )
                    )
                    continue

            if not isinstance(k[2], str):
                sizes = [s.strip() for s in k[2] if s]
                sizes = [s for s in sizes if s]
                sizes = list(sizes)
            elif k[2] == "all":
                sizes = array.coords["size"].values
            else:
                if k[2] in array.coords["size"].values:
                    sizes = [k[2]]
                elif all(
                    s for s in k[2].split(", ") if s in array.coords["size"].values
                ):
                    sizes = [s for s in k[2].split(", ")]
                else:
                    print(
                        "{} is not a recognized size category. It will be skipped.".format(
                            k[2]
                        )
                    )
                    continue

            param = k[3]

            if not param in array.coords["parameter"].values:
                print(
                    "{} is not a recognized parameter. It will be skipped.".format(
                        param
                    )
                )
                continue

            val = d[k]

            distr_dic = {
                "triangular": 5,
                "lognormal": 2,
                "normal": 3,
                "uniform": 4,
                "none": 1,
            }
            distr = distr_dic[k[4]]

            year = set([v[0] for v in val])

            for y in year:
                # No uncertainty parameters given
                if distr == 1:
                    # There should be at least a `loc`
                    if ~np.isnan(val[(y, "loc")]):
                        for s in sizes:
                            for p in pt:
                                array.loc[
                                    dict(
                                        powertrain=p,
                                        size=s,
                                        year=y,
                                        parameter=param,
                                    )
                                ] = val[(y, "loc")]
                    # Otherwise warn
                    else:
                        print("`loc`parameter missing for {} in {}.".format(param, y))
                        continue

                elif distr in [2, 3, 4, 5]:
                    # Check if the correct parameters are present
                    # Triangular

                    if distr == 5:
                        if (
                            np.isnan(val[(y, "loc")])
                            or np.isnan(val[(y, "minimum")])
                            or np.isnan(val[(y, "maximum")])
                        ):
                            print(
                                "One or more parameters for the triangular distribution is/are missing for {} in {}.\n"
                                "The parameter is skipped and default value applies".format(
                                    param, y
                                )
                            )
                            continue

                    # Lognormal
                    if distr == 2:
                        if np.isnan(val[(y, "loc")]) or np.isnan(val[(y, "scale")]):
                            print(
                                "One or more parameters for the lognormal distribution is/are missing for {} in {}.\n"
                                "The parameter is skipped and default value applies".format(
                                    param, y
                                )
                            )
                            continue

                    # Normal
                    if distr == 3:
                        if np.isnan(val[(y, "loc")]) or np.isnan(val[(y, "scale")]):
                            print(
                                "One or more parameters for the normal distribution is/are missing for {} in {}.\n"
                                "The parameter is skipped and default value applies".format(
                                    param, y
                                )
                            )
                            continue

                    # Uniform
                    if distr == 4:
                        if np.isnan(val[(y, "minimum")]) or np.isnan(
                            val[(y, "maximum")]
                        ):
                            print(
                                "One or more parameters for the uniform distribution is/are missing for {} in {}.\n"
                                "The parameter is skipped and default value applies".format(
                                    param, y
                                )
                            )
                            continue

                    a = sa.UncertaintyBase.from_dicts(
                        {
                            "loc": val[y, "loc"],
                            "scale": val[y, "scale"],
                            "shape": val[y, "shape"],
                            "minimum": val[y, "minimum"],
                            "maximum": val[y, "maximum"],
                            "uncertainty_type": distr,
                        }
                    )

                    # Stochastic mode
                    if array.sizes["value"] > 1:
                        rng = sa.MCRandomNumberGenerator(a)

                        for s in sizes:
                            for p in pt:
                                array.loc[
                                    dict(powertrain=p, size=s, year=y, parameter=param)
                                ] = rng.generate(array.sizes["value"]).reshape((-1,))
                    else:
                        dist = sa.uncertainty_choices[distr]
                        median = float(dist.ppf(a, np.array((0.5,))))

                        for s in sizes:
                            for p in pt:
                                array.loc[
                                    dict(powertrain=p, size=s, year=y, parameter=param)
                                ] = median

                else:
                    print(
                        "The uncertainty type is not recognized for {} in {}.\n "
                        "The parameter is skipped and default value applies".format(
                            param, y
                        )
                    )
                    continue
