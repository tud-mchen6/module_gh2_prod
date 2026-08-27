

rule get_hydrogen_curve:
    message:
        "Calculate the hydrogen production curve given inputs."
    params:
        # TODO: add the reading of optional params
        electrolyser_type=config["electrolyser_type"],
    input:
        # TODO: temporary file, configure the wiring later!
        vRES_curves="resources/user/shapes/{shape}/processed_curves_data.parquet",
        # TODO: temporary file, configure the wiring later! Especially that the files have assumptions in
        water_curve="resources/user/shapes/{shape}/water_curve_{shape}_comp.csv",
        water_need=rules.get_shape_water_need.output[0],
    output:
        # TODO: temporary file, configure the wiring later!
        h2_curve="results/{shape}/h2_curve.parquet",
    log:
        "logs/get_hydrogen_curve_{shape}.log",
    script:
        "../scripts/get_hydrogen_curve.py"
