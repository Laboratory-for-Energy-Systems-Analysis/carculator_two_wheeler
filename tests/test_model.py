from pathlib import Path

import numpy as np
import pandas as pd

from carculator_two_wheeler import *

DATA = Path(__file__, "..").resolve() / "fixtures" / "two_wheelers_values.xlsx"
OUTPUT = Path(__file__, "..").resolve() / "fixtures" / "test_model_results.xlsx"
ref = pd.read_excel(DATA, index_col=0)


twip = TwoWheelerInputParameters()
twip.static()
dcts, arr = fill_xarray_from_input_parameters(twip)
twm = TwoWheelerModel(arr)
twm.set_all()


def test_model_results():
    list_powertrains = [
        "Human",
        "ICEV-p",
        "BEV",
    ]
    list_sizes = [
        "Bicycle <25",
        "Bicycle <45",
        "Bicycle cargo",
    ]
    list_years = [
        2020,
    ]

    l_res = []

    for pwt in list_powertrains:
        for size in list_sizes:
            for year in list_years:
                for param in twm.array.parameter.values:
                    val = float(
                        twm.array.sel(
                            powertrain=pwt,
                            size=size,
                            year=year,
                            parameter=param,
                            value=0,
                        ).values
                    )

                    try:
                        ref_val = (
                            ref.loc[
                                (ref["powertrain"] == pwt)
                                & (ref["size"] == size)
                                & (ref["parameter"] == param),
                                year,
                            ]
                            .values.astype(float)
                            .item(0)
                        )
                    except:
                        ref_val = 1

                    _ = lambda x: np.where(ref_val == 0, 1, ref_val)
                    diff = val / _(ref_val)
                    l_res.append([pwt, size, year, param, val, ref_val, diff])

    pd.DataFrame(
        l_res,
        columns=["powertrain", "size", "year", "parameter", "val", "ref_val", "diff"],
    ).to_excel(OUTPUT)


def test_lcia():
    ic = InventoryTwoWheeler(twm)
    ic.calculate_impacts()
