#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import time
import json
import codecs
import logging
import openpyxl
from backports import csv
from openpyxl import Workbook
from acrcloud_filter_libary import FilterWorker
from acrcloud_logger import AcrcloudLogger
from acrcloud.recognizer import ACRCloudRecognizer

if sys.version_info.major == 2:
    reload(sys)
    sys.setdefaultencoding("utf8")

class ACRCloud_Scan_Files:

    def __init__(self, config, debug=1):
        self.openpyxl_version = ".".join(str(openpyxl.__version__).split(".")[:2])
        self.config = config
        self.debug = debug
        self.init_log()
        self.re_handler = ACRCloudRecognizer(self.config)

    def init_log(self):
        log_level = logging.ERROR
        if self.debug == 1:
            log_level = logging.DEBUG

        shandler = logging.StreamHandler()
        #shandler.setLevel(log_level)
        self.log = logging.getLogger("ACRCloud_ScanFile")
        self.log.setLevel(log_level)
        self.log.addHandler(shandler)

    def as_text(self, value):
        if value is None:
            return ""
        return str(value)

    def get_duration_by_file(self, filepath):
        return int(ACRCloudRecognizer.get_duration_ms_by_file(filepath)/1000)

    def export_to_xlsx(self, result_list, export_filename="ACRCloud_ScanFile_Results.xlsx", export_dir="./"):
        try:
            results = []
            for item in result_list:
                filename = item["file"]
                timestamp = item["timestamp"]
                jsoninfo = item["result"]
                if "status" in jsoninfo and jsoninfo["status"]["code"] == 0:
                    row = self.parse_data(jsoninfo)
                    row = [filename, timestamp] + list(row)
                    results.append(row)
            results = sorted(results, key=lambda x:x[1])

            wb = Workbook()
            sheet_music = wb.active
            sheet_music.title = "ACRCloud_Scan_File"

            header_row = ['filename', 'timestamp', 'custom_files_title', 'custom_acrid', 'title', 'artists', 'album',
                        'acrid', 'played_duration', 'label', 'isrc', 'upc', 'deezer', 'spotify', 'itunes', 'youtube']

            sheet_music.append(header_row)
            for row in results:
                sheet_music.append(row)

            for column_cells in sheet_music.columns:
                length = max(len(self.as_text(cell.value)) for cell in column_cells)
                if length > 80:
                    length == 80
                if self.openpyxl_version >= "2.6":
                    sheet_music.column_dimensions[column_cells[0].column_letter].width = length
                else:
                    sheet_music.column_dimensions[column_cells[0].column].width = length

            export_filepath = os.path.join(export_dir, export_filename)
            wb.save(export_filepath)
            if self.debug:
                self.log.info("export_to_xlsx.Save Data to xlsx: {0}".format(export_filename))
        except Exception as e:
            self.log.error("Error@export_to_xlsx", exc_info=True)

    def export_to_csv(self, result_list, export_filename="ACRCloud_ScanFile_Results.csv", export_dir="./"):
        try:
            results = []
            for item in result_list:
                filename = item["file"]
                timestamp = item["timestamp"]
                jsoninfo = item["result"]
                if "status" in jsoninfo and jsoninfo["status"]["code"] == 0:
                    row = self.parse_data(jsoninfo)
                    row = [filename, timestamp] + list(row)
                    results.append(row)

            results = sorted(results, key=lambda x:x[1])

            export_filepath = os.path.join(export_dir, export_filename)

            with codecs.open(export_filepath, 'w', 'utf-8-sig') as f:
                head_row = ['filename', 'timestamp',  'custom_files_title', 'custom_acrid', 'title', 'artists', 'album',
                        'acrid', 'played_duration', 'label', 'isrc', 'upc', 'deezer', 'spotify', 'itunes', 'youtube']
                dw = csv.writer(f)
                dw.writerow(head_row)
                dw.writerows(results)
                if self.debug:
                    self.log.info("export_to_csv.Save Data to csv: {0}".format(export_filename))
        except Exception as e:
            self.log.error("Error@export_to_csv", exc_info=True)

    def parse_data(self, jsoninfo):
        try:
            title, played_duration, isrc, upc, acrid, label, album = [""]*7
            artists, deezer, spotify, itunes, youtube, custom_files_title, audio_id, custom_acrid  = [""]*8

            metadata = jsoninfo.get('metadata', {})
            played_duration = metadata.get("played_duration", "")
            if "music" in metadata and len(metadata["music"]) > 0:
                item = metadata["music"][0]
                title = item.get("title", "")
                offset = item.get("play_offset_ms", "")
                isrc = item.get("external_ids", {"isrc":""}).get("isrc","")
                upc = item.get("external_ids", {"upc":""}).get("upc","")
                acrid = item.get("acrid","")
                label = item.get("label", "")
                album = item.get("album", {"name":""}).get("name", "")
                artists =  ",".join([ ar["name"] for ar in item.get('artists', [{"name":""}]) if ar.get("name") ])
                deezer = item.get("external_metadata", {"deezer":{"track":{"id":""}}}).get("deezer", {"track":{"id":""}}).get("track", {"id":""}).get("id", "")
                spotify = item.get("external_metadata", {"spotify":{"track":{"id":""}}}).get("spotify", {"track":{"id":""}}).get("track", {"id":""}).get("id", "")
                itunes = item.get("external_metadata", {"itunes":{"track":{"id":""}}}).get("itunes", {"track":{"id":""}}).get("track", {"id":""}).get("id", "")
                youtube = item.get("external_metadata", {"youtube":{"vid":""}}).get("youtube", {"vid":""}).get("vid", "")

            if "custom_files" in metadata and len(metadata["custom_files"]) > 0:
                custom_item = metadata["custom_files"][0]
                custom_files_title = custom_item.get("title", "")
                audio_id = custom_item.get("audio_id", "")
                custom_acrid = custom_item.get("acrid", "")
        except Exception as e:
            self.log.error("Error@parse_data")

        res = (custom_files_title, custom_acrid, title, artists, album, acrid,
               played_duration, label, isrc, upc, deezer, spotify, itunes, youtube,)

        return res

    def apply_filter(self, results):
        fworker = FilterWorker()
        result_new = fworker.apply_filter(results)
        return result_new

    def do_recognize(self, filepath, start_time, rec_length):
        current_time = time.strftime('%H:%M:%S', time.gmtime(start_time))
        res_data = self.re_handler.recognize_by_file(filepath, start_time, rec_length)
        return filepath, current_time, res_data

    def for_recognize_file(self,  filepath, start_time, stop_time, step, rec_length):
        try:
            for i in range(start_time, stop_time, step):
                filep, current_time, res_data = self.do_recognize(filepath, i, rec_length)
                if res_data:
                    jsoninfo = json.loads(res_data)
                    if "metadata" in jsoninfo and "timestamp_utc" in jsoninfo["metadata"]:
                        jsoninfo["metadata"]["timestamp_utc"] = current_time
                else:
                    jsoninfo = {}
                yield {"timestamp":current_time, "rec_length":rec_length, "result":jsoninfo, "file":filep}
        except Exception as e:
            self.log.error("Error@for_recognize_file", exc_info=True)

    def recognize_file(self, filepath, start_time, stop_time, step, rec_length):
        try:
            result_list = []
            for i in range(start_time, stop_time, step):
                filep, current_time, res_data = self.do_recognize(filepath, i, rec_length)
                if res_data:
                    jsoninfo = json.loads(res_data)
                    try:
                        if "metadata" in jsoninfo and "timestamp_utc" in jsoninfo["metadata"]:
                            jsoninfo["metadata"]["timestamp_utc"] = current_time

                        code = jsoninfo["status"]["code"]
                        msg = jsoninfo["status"]["msg"]
                        if jsoninfo["status"]["code"] not in [0, 1001]:
                            raise Exception("recognize_file.(timestamp: {0}, {1}, {2})".format(current_time, code, msg))
                    except Exception as e:
                        if self.debug:
                            self.log.error(e)
                        else:
                            print (e)
                        if code in [3001, 3003, 3013]:
                            break
                        else:
                            continue

                    result_list.append({"timestamp":current_time, "rec_length":rec_length, "result":jsoninfo, "file":filep})
                    if self.debug:
                        parse_info = self.parse_data(jsoninfo)
                        self.log.info('recognize_file.(timestamp: {0}, title: {1})'.format(current_time, parse_info[0]))
        except Exception as e:
            self.log.error("Error@recognize_file", exc_info=True)
        return result_list
