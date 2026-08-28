

rule get_hydrogen_curve:
    message:
        "Calculate the hydrogen production curve given inputs."
    params:
        # TODO: add the reading of optional params
        electrolyser_type=config["electrolyser_type"],
        discount_rate=config["discount_rate"],
    input:
        # TODO: temporary file, configure the wiring later!
        vRES_curves="<vres_prod_dir>/shapes/{shape}/processed_curves_data_{pop_year}_{population_scenario}_{demand_scenario}.parquet",
        # TODO: temporary file, configure the wiring later! Especially that the files have assumptions in
        water_curve="<water_curve_dir>/water_curve_{shape}_{water_scenario}.csv",
        water_need=rules.get_shape_water_need.output[0],
    output:
        # TODO: temporary file, configure the wiring later!
        h2_curve="<results>/{shape}/h2_curve_{water_scenario}_{pop_year}_{population_scenario}_{demand_scenario}.parquet",
    log:
        "<logs>/get_hydrogen_curve_{shape}_{water_scenario}_{pop_year}_{population_scenario}_{demand_scenario}.log",
    script:
        "../scripts/get_hydrogen_curve.py"
