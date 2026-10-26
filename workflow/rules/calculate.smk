

rule get_hydrogen_curve:
    message:
        "Calculate the hydrogen production curve given inputs."
    params:
        # TODO: add the reading of optional params
        config=config,
        shape_override_config=lambda wildcards: config.get("overrides", {}).get(wildcards.shape, {}),
    input:
        vres_curves="<vres_prod_dir>/{shape}/processed_curves_data_{demand_scenario}.parquet",
        water_curve="<water_curve_dir>/water_curve_{shape}_{water_scenario}.csv",
        water_need=rules.get_shape_water_need.output[0],
        # script=workflow.source_path("../scripts/get_hydrogen_curve.py"),
    output:
        h2_curve="<results>/{shape}/h2_curve_{water_scenario}_{demand_scenario}.parquet",
    log:
        "<logs_scenarios>/get_hydrogen_curve_{shape}_{water_scenario}_{demand_scenario}.log",
    script:
        "../scripts/get_hydrogen_curve.py"
