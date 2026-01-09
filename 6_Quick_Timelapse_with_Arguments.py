import ee
import geemap
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path='.env')
project_name = os.getenv("project_name")
print(f"Project Name: {project_name}")
ee.Initialize(project=project_name)

rectangle_top_left_input = input("Enter top left corner coordinates (longitude, latitude) separated by a comma: ")
rectangle_bottom_right_input = input("Enter bottom right corner coordinates (longitude, latitude) separated by a comma: ")

top_left = [float(coord) for coord in rectangle_top_left_input.split(',')]
bottom_right = [float(coord) for coord in rectangle_bottom_right_input.split(',')]

region = ee.Geometry.Rectangle([top_left[1], bottom_right[0], bottom_right[1], top_left[0]])


#collecting data
s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") #Sentinel-2 Surface Reflectance data

filtered_image = s2 \
    .filterBounds(region) \
    .sort('system:time_start')\
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
    #.filterDate('2022-01-01', '2022-12-31') \
    

print(f"Number of images found: {filtered_image.size().getInfo()}")

#now making sure they have full coverage of the region
strict_collection = filtered_image.filter(ee.Filter.contains(
        leftField='.geo', #.geo refers to the geometry of the image
        rightValue=region #the region we defined earlier 
    )
)

print(f"Number of images with full coverage: {strict_collection.size().getInfo()}")

min_timestamp = strict_collection.aggregate_min("system:time_start")
max_timestamp = strict_collection.aggregate_max("system:time_start")
# print(f"Min Timestamp: {min_timestamp.getInfo()}")
# print(f"Max Timestamp: {max_timestamp.getInfo()}")
print('First Date:', ee.Date(min_timestamp).format('YYYY-MM-dd').getInfo())
print('Last Date:', ee.Date(max_timestamp).format('YYYY-MM-dd').getInfo())


visualized_collection = strict_collection.map(lambda img: img.visualize(
    bands=['B4', 'B3', 'B2'],
    min=0,
    max=3000
))


import datetime


now = datetime.datetime.now()
time_stamp = now.strftime("%Y_%m_%d_%H_%M_%S")

file_prefix = input("Enter file prefix for the export: ")

file_name = file_prefix + time_stamp
print('Exporting file as:', file_name)

# Create the export task
task = ee.batch.Export.video.toDrive(
    collection=visualized_collection,
    folder='GEE_Exports',
    description=file_name,
    dimensions=720,    
    framesPerSecond=10, 
    region=region
)

task.start()

from tqdm import tqdm
import time

try:
    with tqdm(desc="Exporting video", unit=" checks") as pbar:
        while task.active():
            pbar.update(1)
            time.sleep(30)
    #print('Done.', task.status())
    print(f"The video is saved in {task.status()['destination_uris'][0]}")
except KeyboardInterrupt:
    print('stopped')