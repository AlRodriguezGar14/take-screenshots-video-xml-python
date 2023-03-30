#!/usr/bin/env python3

import json
import subprocess
import math
import os
import concurrent.futures
import xml.etree.ElementTree as ET
import cv2
from xml_ns import xml_ns as ns0

def get_video_metadata(input_video):
    ffprobe_cmd = f'ffprobe -v quiet -print_format json -show_streams {input_video}'.split()
    result = subprocess.run(ffprobe_cmd, capture_output=True)
    metadata = json.loads(result.stdout)
    return metadata

input_video = input('Enter the path to the input video file: ').strip()

# Get video metadata and cache it
metadata = get_video_metadata(input_video)

numerator, denominator = map(int, metadata['streams'][0]['r_frame_rate'].split('/'))
fps = math.floor(numerator / denominator)
if fps == 23:
    fps = 24
if fps == 29:
    fps = 30

# Ask the user for the path to the XML file
xml_file_path = input('Enter the path to the XML file: ').strip()

# Define namespace -> important to let the app understand the xml
ns = {'ns0': ns0}
# Parse the XML file to extract the timecodes
tree = ET.parse(xml_file_path)
root = tree.getroot()

# See the whole document. Important for debuggin and searching
# ET.dump(root)

timecodes = []
for artwork_time in root.findall('.//ns0:artwork_time', ns):
    if artwork_time.text is not None:
        timecode = artwork_time.text.strip()
        timecodes.append(timecode)
print(timecodes)

# Create a temporary folder to store the output images
output_folder = './tmp-previews'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Define a function that generates a preview image for a given timecode
def generate_preview_image(timecode):
    
    hours, minutes, seconds, frames = map(int, timecode.split(':'))
    target_frame_num = (hours * 3600 * fps) + (minutes * 60 * fps) + (seconds * fps) + frames # Calculate the target frame number
    cap = cv2.VideoCapture(input_video)
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_num)
    print(target_frame_num)

    # Seek to the nearest keyframe before the target frame
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_num = cap.get(cv2.CAP_PROP_POS_FRAMES)
        if frame_num >= target_frame_num:
            break
        if cap.get(cv2.CAP_PROP_POS_AVI_RATIO) >= 1.0:
            break

    # Save the current frame as the preview image
    output_image = os.path.join(output_folder, f'{timecode}.jpg')
    cv2.imwrite(output_image, frame)

    cap.release()

    print(f'Printed the preview image for {timecode}')

# Generate preview images using multiple threads
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = []
    for timecode in timecodes:
        futures.append(executor.submit(generate_preview_image, timecode))
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
