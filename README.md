# [Audio Recognition](https://www.acrcloud.com/music-recognition) -- File Scan Tool (Python Script)



## Overview
  [ACRCloud](https://www.acrcloud.com/) provides [Automatic Content Recognition](https://www.acrcloud.com/docs/introduction/automatic-content-recognition/) services for [Audio Fingerprinting](https://www.acrcloud.com/docs/introduction/audio-fingerprinting/) based applications such as **[Audio Recognition](https://www.acrcloud.com/music-recognition)** (supports music, video, ads for both online and offline), **[Broadcast Monitoring](https://www.acrcloud.com/broadcast-monitoring)**, **[Second Screen](https://www.acrcloud.com/second-screen-synchronization)**, **[Copyright Protection](https://www.acrcloud.com/copyright-protection-de-duplication)** and etc.<br>
  
  This tool can scan audio/video files and detect audios you want to recognize such as music, ads.

  Supported Format:
  
>>Audio: mp3, wav, m4a, flac, aac, amr, ape, ogg ...<br>
>>Video: mp4, mkv, wmv, flv, ts, avi ...

## Requirements

**Notice: This tool only support Python 2.**

- Python 2.x
- fuzzywuzzy
- openpyxl
- backports.csv
- requests
- Follow one of the tutorials to create a project and get your host, access_key and access_secret.

 * [How to identify songs by sound](https://www.acrcloud.com/docs/tutorials/identify-music-by-sound/)
 
 * [How to detect custom audio content by sound](https://www.acrcloud.com/docs/tutorials/identify-audio-custom-content/)
 
## Run as a Docker Container
- Install Docker 
  - If you are using Windows: Download [Docker Desktop for Windows](https://download.docker.com/win/stable/Docker%20for%20Windows%20Installer.exe) and install.
  - If you are using MacOs: Download [Docker Desktop for Mac](https://download.docker.com/mac/stable/Docker.dmg) and install.
  - If you are using Linux: Open the Terminal and input `bash <(curl -s https://get.docker.com/)`
- Change the config file (config.json).
- Run following command 
  ```
  git clone https://github.com/acrcloud/acrcloud_scan_files_python.git
  
  cd acrcloud_scan_files_python
  
  sudo docker build -t acrcloud/python_scan_tool .
  # Call it without arguments to display the full help
  sudo docker run --rm acrcloud/python_scan_tool
  
  # Basic usage
  sudo docker run --rm -v $(pwd):/tmp -v /Users/acrcloud/:/music/ acrcloud/python_scan_tool -f /music/test.mp4 -o /tmp
  
  You need to change /Users/acrcloud/ to the directory where your audio/video file is.
  And the report file will in the acrcloud_scan_files_python directory.
  ```
## Installation 
 
 For Windows System, you must install [Python](https://www.python.org/downloads/windows/) and [pip](https://pip.pypa.io/en/stable/installing/).
 
 Open your terminal and change to the script directory of <strong>acrcloud_scan_files_python-master</strong>. Then run the command: 
 
 ```
pip install -r requirements.txt
 ```
## Install ACRCloud Python SDK 
 

 You can run the following command to install it.

 ```
 python -m pip install git+https://github.com/acrcloud/acrcloud_sdk_python
 ```

 Or you can download the sdk and install it by following command.

 [ACRCloud Python SDK](https://github.com/acrcloud/acrcloud_sdk_python).


 ```
 sudo python setup.py install
 ```

## For Windows

### Install Library
 Windows Runtime Library
 
 X86: [download and install Library(windows/vcredist_x86.exe)](https://www.microsoft.com/en-us/download/details.aspx?id=5555)
 
 x64: [download and install Library(windows/vcredist_x64.exe)](https://www.microsoft.com/en-us/download/details.aspx?id=14632)

 
## Usage for Scan File Tool: 

        _    ____ ____   ____ _                 _
       / \  / ___|  _ \ / ___| | ___  _   _  __| |
      / _ \| |   | |_) | |   | |/ _ \| | | |/ _` |
     / ___ \ |___|  _ <| |___| | (_) | |_| | (_| |
    /_/   \_\____|_| \_\\____|_|\___/ \____|\____|
 
 Before you use this script,you must have acrcloud host,access_key and access_secret.
 If you haven't have these ,you can register one https://console.acrcloud.com/signup
 
 Change the content of config.json,fill in your host, access_key and access_secret
 ```
{
  "host": "xxxxx",
  "access_key": "xxxxx",
  "access_secret": "xxxxx"
}
 ```
 
 ```
 python acrcloud_scan_files_python.py -d folder_path
 python acrcloud_scan_files_python.py -f file_path
 python acrcloud_scan_files_python.py -h get_usage_help
 ```

### Scan Folder Example:
 ```
 python acrcloud_scan_files_python.py -d ~/music
 ```
### Scan File Example: 
 ```
 python acrcloud_scan_files_python.py -f ~/testfiles/test.mp3
 ```
 
### Add more params

"-s" ---- scan step. （The scan interval.）

"-l" ---- recongizing length.  (use how many seconds to recongize. for example: -s 20 -l 10, it will get 20 seconds of audio each time and use the first 10 seconds of audio to recognize)

"-r" ---- scan range. （The scan range. for example: -r 5-20, it will recognize the file starting from the 5th second and finish at the 20th second.）

"-c" ---- set the config file path.

"-w" ---- results with duration. (1-yes, 0-no), you must set offset config for your access key, pls contact support@acrcloud.com

"-o" ---- set the directory to save the results

"-t" ---- set the type of file.(csv[default] or xlsx).
 ```
 If you want to change scan interval or you want to set recognize range,you can add some params
 Example:
     python acrcloud_scan_files_python.py -f ~/testfiles/test.mp3 -s 30 -r 0-20
     python acrcloud_scan_files_python.py -d ~/music -s 30 -w 1
 ```

Default is scan folder where this script in.

The results are saved in the folder where this script in.


## Usage for Scan File Libary

Introduction all API.

### acrcloud_scan_files_libary.py

 ```
 class ACRCloud_Scan_Files:
     def get_duration_by_file(self, filepath):
        #@param filepath : query file path
        #@return : total duration of the file

     def export_to_xlsx(self, result_list, export_filename, export_dir):
        #@param result_list : the list of identification results
        #@param export_filename : export to this file
        #@param export_dir : export to this directory

     def export_to_csv(self, result_list, export_filename, export_dir):
        #@param result_list : the list of recognition results
        #@param export_filename : export to this file
        #@param export_dir : export to this directory

     def parse_data(self, result):
        #@param result : one recognition result
        #@return : a tuple, as follow
        #     (title, artists, album, acrid, played_duration, label, isrc, upc,
        #       deezer, spotify, itunes, youtube, custom_files_title, audio_id)

     def apply_filter(self, results):
        #@param results : the list of recognition results
        #@return : a list results with played_duration

     def for_recognize_file(self, filepath, start_time, stop_time, step, rec_length):
        #@param filepath : query file path
        #@param start_time : the start offset to recognize (seconds)
        #@param stop_time : the end offset to recognize (seconds)
        #@param rec_length : the duration of each fragment to recognize
        #@return : iterator to return the each recognition result

     def recognize_file(self, filepath, start_time, stop_time, step, rec_length):
        #@param filepath : query file path
        #@param start_time : the start offset to recognize (seconds)
        #@param stop_time : the end offset to recognize (seconds)
        #@param rec_length : the duration of each fragment to recognize
        #@return : the list of recognition results
 ```

### Example

run Text: python example.py test.mp3

 ```
 #!/usr/bin/env python
 #-*- coding:utf-8 -*-

 import os
 import sys
 from acrcloud_scan_files_libary import ACRCloud_Scan_Files

 if __name__ == "__main__":

    #ACRCloud Scan File Example
    is_debug = 1   #display the log info, or is_debug=0
    start_time = 0 #scan file start time(seconds)
    stop_time = 0  #scan file end time(seconds), or you can set it to the duration of file
    step = 10      #the length of each identified fragment (seconds)
    rec_length = step

    #your acrcloud project host, access_key, access_secret
    config = {
        "host": "XXX",
        "access_key":"XXX",
        "access_secret": "XXX"
    }

    filepath = sys.argv[1]

    acr_sfile = ACRCloud_Scan_Files(config, is_debug)

    stop_time = acr_sfile.get_duration_by_file(filepath)

    #get a list of recognition results
    result_list = acr_sfile.recognize_file(filepath, start_time, stop_time, step, rec_length)

    #export the result
    export_dir = "./"
    #export to csv
    export_filename_csv = "test.csv"
    acr_sfile.export_to_csv(result_list, export_filename_csv, export_dir)
    #export to xlsx
    export_filename_xlsx = "test.xlsx"
    acr_sfile.export_to_xlsx(result_list, export_filename_xlsx, export_dir)

    #iterator to get the result of each fragment
    result_list2 = []
    for item in acr_sfile.for_recognize_file(filepath, start_time, stop_time, step, rec_length):
        result_list2.append(item)
        filename = item["file"]
        timestamp = item["timestamp"]
        res = acr_sfile.parse_data(item["result"])
        title = res[0]
        print filename, timestamp, title

    #get results with played-duration
    filter_results = acr_sfile.apply_filter(result_list2)
    #export the results to xlsx
    export_filtername_xlsx = "test_with_duration.xlsx"
    acr_sfile.export_to_xlsx(filter_results, export_filtername_xlsx, export_dir)
 ```
