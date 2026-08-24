"""Turn the csv into GeoTIFF for clipping.
Note that it's not sure if the GeoTIFF is ESG:4326, but we have to assume it is.
"""

import pandas as pd
import xarray as xr
import rioxarray


def reform_water_need(csv, water_need_tiff):

    df = pd.read_csv(csv).rename(columns={"longitude": "y", "latitude": "x"})
    # Get rid of duplicates
    df = df.drop_duplicates(subset=["y", "x"], keep="first")
    da = df.set_index(["y", "x"])["Water_Consumption"].to_xarray()
    da = da.sortby("y", ascending=False)
    da.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
    da.rio.write_crs("EPSG:4326", inplace=True)
    da.rio.to_raster(water_need_tiff)


if __name__ == "__main__":
    reform_water_need(
        csv=snakemake.input.csv, water_need_tiff=snakemake.output.water_need_tiff
    )
