"""
Parse the clipped raster to get shape average water need per kg H2 produced.
"""

import numpy as np
import xarray as xr
import rioxarray


def get_shape_water_need(clipped, shape_water_need):

    arr_shape_need = xr.open_dataarray(clipped).values
    arr_shape_need = arr_shape_need[~np.isnan(arr_shape_need)]
    with open(shape_water_need, "w") as f:
        f.write(str(np.average(arr_shape_need)))


if __name__ == "__main__":
    get_shape_water_need(
        clipped=snakemake.input.clipped,
        shape_water_need=snakemake.output.shape_water_need,
    )
