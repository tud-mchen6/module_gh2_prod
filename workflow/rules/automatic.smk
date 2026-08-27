"""Rules to used to download automatic resource files."""



rule download_water_need:
    message:
        """
        Download the rasterised data of water consumption per kg H2 produced,
        with the source Wortmann et al. 2026.
        """
    params:
        url=internal['resources']['automatic']['water_need']
    output:
        "<resources>/automatic/global/water_need.zip",
    log:
        "<logs>/download_water_need.log",
    shell:
        """
        curl -sSLo {output:q} {params.url:q}
        """


rule extract_water_need:
    message:
        """
        Unzip and extract the yearly average water need data from the zip.
        """
    input:
        rules.download_water_need.output[0],
    params:
        internal_paths='cooling-water-hydrogen-replication/data/figure_source_data/cooling/Yearly_Average.csv'
    output:
        temp('<resources>/automatic/global/water_need_world.csv'),
    log:
        "<logs>/extract_water_need.log",
    wrapper:
        "v9.8.0/utils/libarchive/extract"


rule reform_water_need:
    message:
        """
        Turn the csv into a raster in GeoTIFF format to get ready for clipping.
        """
    input:
        csv=rules.extract_water_need.output[0],
    output:
        water_need_tiff=temp("<resources>/automatic/global/water_need_world.tif"),
    log:
        '<logs>/reform_water_need.log',
    script:
        "../scripts/reform_water_need.py"

rule clip_shape_water_need:
    message:
        """
        Use the raster of a region/country to clip the rasterised water need file.
        """
    input:
        raster="<resources>/automatic/global/water_need_world.tif",
        like_raster='<resources>/user/shapes/{shape}/area_potential_pv_rooftop.tif',
    output:
        path=temp("<resources>/automatic/cutout/{shape}/water_need.tif"),
    log:
        "<logs>/clip_shape_water_need_{shape}.log",
    wrapper:
        "v9.0.0/geo/rasterio/clip"


rule get_shape_water_need:
    message:
        """
        Use the clipped raster water need file to get the shape average of 
        yearly average H2 production need per kg H2.
        """
    input:
        clipped=rules.clip_shape_water_need.output[0],
    output:
        shape_water_need=temp("<resources>/automatic/cutout/{shape}/water_need.txt"),
    log:
        "<logs>/get_shape_water_need_{shape}.log",
    script:
        "../scripts/get_shape_water_need.py"