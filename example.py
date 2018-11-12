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
        "host": "your project host",
        "access_key":"your project access_key",
        "access_secret": "your project access_secret"
    }

    filepath = sys.argv[1]

    acr_sfile = ACRCloud_Scan_Files(config, is_debug)

    stop_time = acr_sfile.get_duration_by_file(filepath)

    #get a list of recognition results
    result_list = acr_sfile.recognize_file(filepath, start_time, stop_time, step, rec_length)

    #export dir
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
        title = res[3]
        print filename, timestamp, title

    #get results with played-duration
    filter_results = acr_sfile.apply_filter(result_list2)
    #export the results to xlsx
    export_filtername_xlsx = "test_with_duration.xlsx"
    acr_sfile.export_to_xlsx(filter_results, export_filtername_xlsx, export_dir)


