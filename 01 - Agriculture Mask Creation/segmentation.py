# importing libraries
import time
from rsgislib.segmentation import shepherdseg
import rsgislib.segmentation as seg
import rasterio as r
import rasterio
from rasterio.features import shapes
import numpy as np
import geopandas as gp
import matplotlib
import numpy as np
from rasterio.mask import mask
import shapely
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import random
import subprocess

# defining the function to write the log to a file
def write_text(text, print_end='\n'):
    with open("/home/bruno.matosak/Semiarido/segmentation_log.txt", 'a+') as f:
        print(text, end=print_end, flush=True)
        f.write(text+print_end)
        
def do_the_segmentation(input_img, ref_path, save_directory, save_file_name):
    t1 = time.time()
    # doing the segmentaton
    write_text('------------------------------------------------------------------------------------------')
    write_text('MAKING THE SEGMENTATION WITH RSGISLIB...\n')

    from rsgislib.segmentation import shepherdseg
    import rsgislib.segmentation as seg

    out_clumps_img = os.path.join(save_directory, f'{save_file_name}.tif')

    write_text(f'Input Image: {input_img}')
    write_text(f'Output Clumps Image: {out_clumps_img}')
    write_text(f'Save File Name: {save_file_name}')
    write_text(f'Reference Path: {ref_path}\n')

    shepherdseg.run_shepherd_segmentation(input_img,
                                          out_clumps_img,
                                          out_mean_img=None,
                                          tmp_dir=save_directory, 
                                          gdalformat='KEA',
                                          calc_stats=False,
                                          no_stretch=False,
                                          no_delete=False,
                                          num_clusters=60,
                                          min_n_pxls=100, 
                                          dist_thres=100, 
                                          bands=None, 
                                          sampling=100, 
                                          km_max_iter=200, 
                                          process_in_mem=False, 
                                          save_process_stats=False, 
                                          img_stretch_stats='', 
                                          kmeans_centres='', 
                                          img_stats_json_file='')

    t2 = time.time()
    write_text("Elapsed time from start: %.3f minutes." % ((t2-t1)/60))

    # georreferencing the cumpls of images
    write_text('------------------------------------------------------------------------------------------')
    write_text('GEORREFERENCING THE CLUMPS IMAGE...\n')

    import rasterio as r

    profile_out = r.open(input_img).profile
    profile_in = r.open(out_clumps_img).profile
    img = r.open(out_clumps_img).read(1)

    out_name_geo = out_clumps_img[:-4]+'_geo.tif'

    profile_out.update({'dtype': profile_in['dtype'], 'count': profile_in['count'], 'compress': 'packbits'})
    with r.open(out_name_geo, 'w', **profile_out) as dst:
            dst.write(img, 1)

    t2 = time.time()
    write_text("Elapsed time from start: %.3f minutes." % ((t2-t1)/60))

    # polygonize raster
    write_text('------------------------------------------------------------------------------------------')
    write_text('POLYGONIZING RASTER...\n')
    import rasterio
    from rasterio.features import shapes
    import numpy as np
    import geopandas as gp

    ref = r.open(ref_path)

    mask = None
    with rasterio.Env():
        with rasterio.open(out_name_geo) as src:
            image = np.asarray(src.read(1), dtype = np.int32) # first band
            results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) 
            in enumerate(
                shapes(image, mask=mask, transform=src.transform)))

    geoms = list(results)

    gpd_polygonized_raster = gp.GeoDataFrame.from_features(geoms)
    gpd_polygonized_raster = gpd_polygonized_raster.set_crs(r.open(input_img).crs)

    import matplotlib
    import numpy as np
    cmap = matplotlib.colors.ListedColormap(np.random.rand(256,3))
    gpd_polygonized_raster.plot(cmap=cmap)

    t2 = time.time()
    write_text("Elapsed time from start: %.3f minutes." % ((t2-t1)/60))

    # iterating through every polygon
    write_text('------------------------------------------------------------------------------------------')
    write_text('ITERATING THROUGH EVERY POLYGON...\n')
    import rasterio as r
    from rasterio.mask import mask
    import shapely
    import numpy as np
    import matplotlib.pyplot as plt

    # iteratinf through every polygon
    percent_iter = 5
    print_percent = 0
    count = 0
    total=len(gpd_polygonized_raster)
    for index, row in gpd_polygonized_raster.iterrows():
        data = np.asarray(mask(ref, [shapely.geometry.mapping(row.geometry)], crop=True, nodata=255)[0], dtype = np.float32)

        qt_0_GDC = np.sum(data[0]==0)
        qt_0_ESA = np.sum(data[1]==0)
        qt_0_MB  = np.sum(data[2]==0)
        qt_1_GDC = np.sum(data[0]==1)
        qt_1_ESA = np.sum(data[1]==1)
        qt_1_MB  = np.sum(data[2]==1)

        gpd_polygonized_raster.at[index, 'qt_0_GDC'] = qt_0_GDC
        gpd_polygonized_raster.at[index, 'qt_0_ESA'] = qt_0_ESA
        gpd_polygonized_raster.at[index, 'qt_0_MB']  = qt_0_MB
        gpd_polygonized_raster.at[index, 'qt_1_GDC'] = qt_1_GDC
        gpd_polygonized_raster.at[index, 'qt_1_ESA'] = qt_1_ESA
        gpd_polygonized_raster.at[index, 'qt_1_MB']  = qt_1_MB

        qt_0_GEM = qt_0_GDC + qt_0_ESA + qt_0_MB
        qt_1_GEM = qt_1_GDC + qt_1_ESA + qt_1_MB
        qt_0_GM = qt_0_GDC + qt_0_MB
        qt_1_GM = qt_1_GDC + qt_1_MB

        gpd_polygonized_raster.at[index, '0_GEM']  = qt_0_GEM
        gpd_polygonized_raster.at[index, '1_GEM']  = qt_1_GEM
        gpd_polygonized_raster.at[index, '0_GM']  = qt_0_GM
        gpd_polygonized_raster.at[index, '1_GM']  = qt_1_GM

        if qt_0_GEM < qt_1_GEM:
            max_GEM = 1
            conf_GEM = 100*qt_1_GEM/(qt_0_GEM+qt_1_GEM)
        else:
            max_GEM = 0
            conf_GEM = 100*qt_0_GEM/(qt_0_GEM+qt_1_GEM)

        if qt_0_GM < qt_1_GM:
            max_GM = 1
            conf_GM = 100*qt_1_GM/(qt_0_GM+qt_1_GM)
        else:
            max_GM = 0
            conf_GM = 100*qt_0_GM/(qt_0_GM+qt_1_GM)

        gpd_polygonized_raster.at[index, 'max_GEM']  = max_GEM
        gpd_polygonized_raster.at[index, 'conf_GEM'] = conf_GEM
        gpd_polygonized_raster.at[index, 'max_GM']   = max_GM
        gpd_polygonized_raster.at[index, 'conf_GM']  = conf_GM

        count += 1

        if 100*count/total >= print_percent:
            write_text(f'{print_percent}...', print_end='')
            print_percent+=percent_iter
    write_text('')
    write_text('Saving... ')
    gpd_polygonized_raster.to_file(os.path.join(save_directory, f'{save_file_name}.shp'))
    write_text('Done!')

    t2 = time.time()
    write_text("Elapsed time from start: %.3f minutes." % ((t2-t1)/60))

    # everything is done
    write_text('------------------------------------------------------------------------------------------')
    write_text('ALL DONE (for now)\n')

    t2 = time.time()
    write_text("Elapsed time from start: %.3f minutes." % ((t2-t1)/60))

t_start = time.time()
    
# doing the iterations
files = glob.glob('/home/bruno.matosak/Semiarido/MultiInput/LULC/LULC_id*.tif')
random.shuffle(files)

# eliminating files that have already been processed
files_done = glob.glob('/home/bruno.matosak/Semiarido/MultiInput/segmentations/segmentation_id*.shp')
for file in files_done:
    file2 = file.replace('segmentations/segmentation', 'LULC/LULC').replace('.shp', '.tif')
    files.remove(file2)

# iterating through all the files to create the reference
count = 1
for file in files:
    # gets the tile's id
    id_ = file.split('d')[-1].split('.')[0]
    # writes stuff
    write_text('==========================================================================================')
    write_text(f'SEGMENTING ID:{id_} ({count}/{len(files)})')
    
    # the big boi, our segmentation
    do_the_segmentation(input_img = file.replace('/LULC/', '/yearly_reduction/').replace('/LULC_', '/Reduction_Optical_Year_'),
                        ref_path = file, 
                        save_directory = '/home/bruno.matosak/Semiarido/MultiInput/segmentations',
                        save_file_name = f'segmentation_id{id_}')
    
    # all done!
    write_text('\n\n')
    count += 1
    
write_text('ALL DONE.')

t_end = time.time()
write_text("Total elapsed time: %.3f hours." % ((t_end-t_start)/3600))