"""A simple script to serve as an example.

Should be deleted in real workflows.
"""

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np


# Default parameters of two electrolyser technologies
# TODO: find sensible numbers
AE_params = {
    "ener": 58,  # kWhe/kg H2
    "CAPEX": 700,  # EUR/kW
    "OPEX": 50,  # EUR/kg
    "life": 20,  # years
    "FOM": 0.02,  # share of CAPEX
}
PEM_params = {
    "ener": 61,  # kWhe/kg H2
    "CAPEX": 800,  # EUR/kW
    "OPEX": 60,  # EUR/kg
    "life": 20,  # years
    "FOM": 0.02,  # share of CAPEX
}


def get_hydrogen_curve(
    electrolyser_type, vRES_curves, water_curve, water_need, h2_curve, discount_rate
):

    # Read the vRES curves. Area in km2; production in MWh
    pf = pq.ParquetFile(vRES_curves)
    vRES_dict = {}
    for name in pf.schema_arrow.names:  # Slowly load the content
        if name == "prod":
            vRES_dict[name] = (
                pf.read(columns=[name])[name].to_numpy() * 1e3
            )  # Change unit to kWh
        else:
            vRES_dict[name] = pf.read(columns=[name])[name].to_numpy()
    # Read the water curve, unit of quantity is 1e9 m3
    water_raw = pd.read_csv(water_curve)
    water = water_raw[water_raw["prod"] > 0]
    water_comp = water_raw[water_raw["prod"] < 0]
    # Read water consumption (1e-3 m3) per kg produced H2
    with open(water_need, "r") as f:
        water_per_kg = float(f.read())
    if electrolyser_type == "AE":
        tech_params = AE_params
    elif electrolyser_type == "PEM":
        tech_params = PEM_params
    shape = snakemake.wildcards.shape
    # TODO: add overwrite values

    # Find out all the water-electricity relations. Unit: kWh/m3
    water["elec_to_water"] = tech_params["ener"] / water_per_kg * 1e3 + water["ener"]

    # Construct the arrays for the final H2 curve
    water_prod = []
    water_cost = []
    vRES_prod = []
    vRES_cost = []
    # Start from the lowest cost vRES
    # TODO: the compensate thing!
    if water["prod"].sum() > 0:
        vRES_prod_total = np.cumsum(vRES_dict["prod"])[-1]
        if len(water["ener"]) > 1:
            # Calculate the step in vRES curve where water curve changes step
            # If vRES curve stops before the water curve changes step
            if (
                vRES_prod_total
                < water["prod"].iloc[0] * water["elec_to_water"].iloc[0] * 1e9
            ):  # kWh
                vRES_prod = vRES_dict["prod"]
                vRES_cost = vRES_dict["lcoe"]
                water_cost = [float(water["cost"].iloc[0])] * len(vRES_dict["prod"])
                water_prod = vRES_prod / water["elec_to_water"].iloc[0]
            else:
                # TODO: change code into iterative or make it much less verbose
                # The first step
                vRES_step_0 = water["prod"].iloc[0] * water["elec_to_water"].iloc[0]
                i = np.searchsorted(np.cumsum(vRES_dict["prod"]), vRES_step_0)
                vRES_prod = vRES_dict["prod"][:i]
                vRES_prod = np.append(
                    vRES_prod, vRES_step_0 - np.cumsum(vRES_dict["prod"])[i - 1]
                )
                vRES_cost = vRES_dict["lcoe"][: i + 1]
                water_cost = [float(water["cost"].iloc[0])] * len(vRES_cost)
                water_prod = vRES_prod / water["elec_to_water"].iloc[0]
                # The second step
                vRES_step_1 = water["prod"].iloc[1] * water["elec_to_water"].iloc[1]
                # If water is the limiting factor
                if (vRES_step_0 + vRES_step_1) < vRES_dict["prod"].sum():
                    ii = np.searchsorted(
                        np.cumsum(vRES_dict["prod"]), vRES_step_0 + vRES_step_1
                    )
                    add_prod = [np.cumsum(vRES_dict["prod"])[i] - vRES_step_0]
                    add_prod = np.append(add_prod, vRES_dict["prod"][i + 1 : ii])
                    add_prod = np.append(
                        add_prod,
                        np.cumsum(vRES_dict["prod"])[i] - vRES_step_0 - vRES_step_1,
                    )
                    vRES_cost = np.append(vRES_cost, vRES_dict["lcoe"][i])
                    vRES_cost = np.append(vRES_cost, vRES_dict["lcoe"][i + 1 : ii])
                    vRES_cost = np.append(vRES_cost, vRES_dict["lcoe"][ii + 1])
                else:
                    add_prod = [np.cumsum(vRES_dict["prod"])[i] - vRES_step_0]
                    add_prod = np.append(add_prod, vRES_dict["prod"][i + 1 :])
                    vRES_prod = np.append(vRES_prod, add_prod)
                    vRES_cost = np.append(vRES_cost, vRES_dict["lcoe"][i])
                    vRES_cost = np.append(vRES_cost, vRES_dict["lcoe"][i + 1 :])
                water_cost = np.append(
                    water_cost, [float(water["cost"].iloc[1])] * (len(add_prod))
                )
                water_prod = np.append(water_prod, add_prod / water["prod"].iloc[1])
        else:
            # See vRES or water total prod is the limiting factor
            water_total = water["prod"].sum() * 1e9  # Unit: m3
            if (
                vRES_prod_total / water_total > water["elec_to_water"].iloc[0]
            ):  # If water is the limiting factor
                vRES_new_total = water_total * water["elec_to_water"].iloc[0]
                i = np.searchsorted(np.cumsum(vRES_dict["prod"]), vRES_new_total)
                vRES_prod = vRES_dict["prod"][:i]
                vRES_prod = np.append(
                    vRES_prod, vRES_new_total - np.cumsum(vRES_dict["prod"])[i - 1]
                )
                vRES_cost = vRES_dict["lcoe"][: i + 1]
                water_cost = [float(water["cost"].iloc[0])] * (i + 1)
            else:  # If vRES is the limiting factor
                vRES_prod = vRES_dict["prod"]
                vRES_cost = vRES_dict["lcoe"]
                water_cost = [float(water["cost"].iloc[0])] * len(vRES_dict["prod"])
            water_prod = vRES_prod / water["elec_to_water"].iloc[0]

        # Calculate LCOH based on given data and the equation
        crf = (
            discount_rate
            * (1 + discount_rate) ** tech_params["life"]
            / ((1 + discount_rate) ** tech_params["life"] - 1)
        )
        gh2_prod = vRES_prod / tech_params["ener"]
        cap = (
            gh2_prod / 8760
        )  # assume same power level all year; conservative assumption
        # Electrolyser CAPEX and FOM
        # TODO: add replacement cost of electrolyser
        tot_cost = (1 + tech_params["FOM"]) * cap * crf * tech_params["CAPEX"]
        # Water and electricity cost
        tot_cost += water_cost * water_prod + vRES_cost * vRES_prod
        gh2_cost = tot_cost / gh2_prod
        # Output to the given path
        table = pa.table(dict({"gh2_prod": gh2_prod, "gh2_cost": gh2_cost}))
    else:
        print(f"No hydrogen can be produced in {shape}. Output empty parquet")
        table = pa.table(dict({"gh2_prod": [], "gh2_cost": []}))
    pq.write_table(table, h2_curve)

    # ### Calculate the total electricity needed when all given water is used up
    # # That includes the part of electrolyser usage, and the part for water production (if present)
    # water_total = water["prod"].sum() * 1e9  # Unit: m3
    # water_energy_total = (
    #     water["prod"] * water["ener"]
    # ).sum() * 1e6  # Unit: MWh (1e9 m3 * kWh/m3)
    # all_energy_for_water = (
    #     water_energy_total
    #     + water_total / water_per_kg * 1e12 * tech_params["ener"] * 1e-3
    # )
    # vRES_prod_total = np.cumsum(vRES_dict["prod"])[-1]


if __name__ == "__main__":
    get_hydrogen_curve(
        electrolyser_type=snakemake.params.electrolyser_type,
        discount_rate=snakemake.params.discount_rate,
        vRES_curves=snakemake.input.vRES_curves,
        water_curve=snakemake.input.water_curve,
        water_need=snakemake.input.water_need,
        h2_curve=snakemake.output.h2_curve,
    )
