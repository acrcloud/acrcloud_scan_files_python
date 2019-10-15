#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import time
import json
import codecs
import optparse
import logging
import openpyxl
from backports import csv
from openpyxl import Workbook
from acrcloud_logger import AcrcloudLogger
from acrcloud_filter_libary import FilterWorker
from acrcloud.recognizer import ACRCloudRecognizer

if sys.version_info.major == 2:
    reload(sys)
    sys.setdefaultencoding("utf8")


class ACRCloud_Scan_Files:

    def __init__(self, config_file):
        self.config = {
            'host': '',
            'access_key': '',
            'access_secret': '',
            'debug': False,
            'timeout': 10  # seconds
        }
        self.openpyxl_version = ".".join(str(openpyxl.__version__).split(".")[:2])
        self.config_file = config_file
        self.init_log()
        self.init_config()

    def init_log(self):
        self.dlog = AcrcloudLogger('ACRCloud_ScanF', logging.INFO)
        if not self.dlog.addFilehandler(logfile="log_scan_files.log", logdir="./", loglevel=logging.WARN):
            sys.exit(1)
        if not self.dlog.addStreamHandler():
            sys.exit(1)

    def init_config(self):
        try:
            json_config = None
            with codecs.open(self.config_file, 'r') as f:
                json_config = json.loads(f.read())
            for k in ["host", "access_key", "access_secret"]:
                if k in json_config and json_config[k].strip():
                    self.config[k] = str(json_config[k].strip())
                else:
                    self.dlog.logger.error("init_config.not found {0} from config.json, pls check".format(k))
                    sys.exit(1)

            self.re_handler = ACRCloudRecognizer(self.config)
            if self.re_handler:
                self.dlog.logger.warning("init_config success!")
        except Exception as e:
            self.dlog.logger.error("init_config.error", exc_info=True)

    def read_file(self, infile, jFirst=True):
        with open(infile, "rb") as rfile:
            for line in rfile:
                if jFirst:
                    jFirst = False
                    continue
                yield line.strip()

    def write_error(self, file_path, error_time, error_detail):
        with open('error_scan.txt', 'a', ) as f:
            msg = file_path + '||' + str(error_time) + '||' + str(error_detail) + '\n'
            f.write(msg)

    def empty_error_scan(self):
        if os.path.exists('error_scan.txt'):
            os.remove('error_scan.txt')

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

            export_filepath = os.path.join(export_dir, export_filename)

            with codecs.open(export_filepath, 'w', 'utf-8-sig') as f:
                head_row = ['filename', 'timestamp', 'title', 'artists', 'album', 'acrid', 'played_duration', 'label',
                            'isrc', 'upc', 'deezer', 'spotify', 'itunes', 'youtube', 'custom_files_title', 'audio_id']
                dw = csv.writer(f)
                dw.writerow(head_row)
                dw.writerows(results)
                self.dlog.logger.info("export_to_csv.Save Data to csv: {0}".format(export_filepath))
        except Exception as e:
            self.dlog.logger.error("Error export_to_csv", exc_info=True)

    def export_to_json(self, result_list, export_filename="ACRCloud_ScanFile_Results.json", export_dir="./"):
        try:
            results = []
            json_results = []
            new_results = {}
            export_filepath = os.path.join(export_dir, export_filename)

            head_row = ['filename', 'timestamp', 'title', 'artists', 'album', 'acrid', 'played_duration', 'label',
                        'isrc', 'upc', 'deezer', 'spotify', 'itunes', 'youtube', 'custom_files_title', 'audio_id']

            for item in result_list:
                filename = item["file"]
                timestamp = item["timestamp"]
                jsoninfo = item["result"]
                if "status" in jsoninfo and jsoninfo["status"]["code"] == 0:
                    row = self.parse_data(jsoninfo)
                    row = [filename, timestamp] + list(row)
                    results.append(row)

            for i in results:
                for k in range(len(head_row)):
                    new_results[head_row[k]] = i[k]

                json_results.append(new_results)

            with codecs.open(export_filepath, 'w', 'utf-8-sig') as f:
                f.write(json.dumps(json_results))
        except Exception as e:
            self.dlog.logger.error("Error export_to_json", exc_info=True)

    def export_to_xlsx(self, result_list, export_filename="ACRCloud_ScanFile_Results.xlsx", export_dir="./"):
        try:
            wb = Workbook()
            sheet_channels = wb.active
            sheet_channels.title = "Results"
            head_row = ['filename', 'timestamp', 'title', 'artists', 'album', 'acrid', 'played_duration', 'label',
                        'isrc', 'upc', 'deezer', 'spotify', 'itunes', 'youtube', 'custom_files_title', 'audio_id']
            sheet_channels.append(head_row)

            for item in result_list:
                filename = item["file"]
                timestamp = item["timestamp"]
                jsoninfo = item["result"]
                if "status" in jsoninfo and jsoninfo["status"]["code"] == 0:
                    row = self.parse_data(jsoninfo)
                    row = [filename, timestamp] + list(row)
                    sheet_channels.append(row)

            export_filepath = os.path.join(export_dir, export_filename)

            for column_cells in sheet_channels.columns:
                length = max(len(str(cell.value) if cell.value else "") for cell in column_cells)
                if length > 100:
                    length == 100
                if self.openpyxl_version >= "2.6":
                    sheet_channels.column_dimensions[column_cells[0].column_letter].width = length
                else:
                    sheet_channels.column_dimensions[column_cells[0].column].width = length
            wb.save(export_filepath)

            self.dlog.logger.info("export_to_xlsx.Save Data to xlsx: {0}".format(export_filepath))
        except Exception as e:
            self.dlog.logger.error("Error export_to_xlsx", exc_info=True)

    def parse_data(self, jsoninfo):
        try:
            title, played_duration, isrc, upc, acrid, label, album = [""] * 7
            artists, deezer, spotify, itunes, youtube, custom_files_title, audio_id = [""] * 7

            metadata = jsoninfo.get('metadata', {})
            played_duration = metadata.get("played_duration", "")
            if "music" in metadata and len(metadata["music"]) > 0:
                item = metadata["music"][0]
                title = item.get("title", "")
                offset = item.get("play_offset_ms", "")
                if "external_ids" in item:
                    if "isrc" in item["external_ids"]:
                        isrc_obj = item["external_ids"]["isrc"]
                        isrc = isrc_obj[0] if type(isrc_obj) == list else isrc_obj
                    if "upc" in item["external_ids"]:
                        upc_obj = item["external_ids"]["upc"]
                        upc = upc_obj[0] if type(upc_obj) == list else upc_obj
                acrid = item.get("acrid", "")
                label = item.get("label", "")
                album = item.get("album", {"name": ""}).get("name", "")
                artists = ",".join([ar["name"] for ar in item.get('artists', [{"name": ""}]) if ar.get("name")])
                if "external_metadata" in item:
                    e_metadata = item["external_metadata"]
                    if "deezer" in e_metadata:
                        deezer_obj = e_metadata["deezer"]
                        deezer = deezer_obj[0]["track"]["id"] if type(deezer_obj) == list else deezer_obj["track"]["id"]
                    if "spotify" in e_metadata:
                        spotify_obj = e_metadata["spotify"]
                        spotify = spotify_obj[0]["track"]["id"] if type(spotify_obj) == list else spotify_obj["track"][
                            "id"]
                    if "youtube" in e_metadata:
                        youtube_obj = e_metadata["youtube"]
                        youtube = youtube_obj[0]["vid"] if type(youtube_obj) == list else youtube_obj["vid"]

            if "custom_files" in metadata and len(metadata["custom_files"]) > 0:
                custom_item = metadata["custom_files"][0]
                custom_files_title = custom_item.get("title", "")
                audio_id = custom_item.get("audio_id", "")
        except Exception as e:
            self.dlog.logger.error("parse_data.error.data:{0}".format(metadata), exc_info=True)

        res = (title, artists, album, acrid, played_duration, label, isrc, upc,
               deezer, spotify, itunes, youtube, custom_files_title, audio_id)
        return res

    def apply_filter(self, results):
        fworker = FilterWorker()
        result_new = fworker.apply_filter(results)
        return result_new

    def do_recognize(self, filepath, start_time, rec_length):
        try:
            current_time = time.strftime('%H:%M:%S', time.gmtime(start_time))
            res_data = self.re_handler.recognize_by_file(filepath, start_time, rec_length)
            return filepath, current_time, res_data
        except Exception as e:
            self.dlog.logger.error("do_recognize.error.({0}, {1}, {2})".format(filepath, start_time, rec_length),
                                   exc_info=True)
        return filepath, current_time, None

    def recognize_file(self, filepath, start_time, stop_time, step, rec_length, with_duration=0):
        self.dlog.logger.warning("scan_file.start_to_run: {0}".format(filepath))

        result = []
        for i in range(start_time, stop_time, step):
            filep, current_time, res_data = self.do_recognize(filepath, i, rec_length)
            try:
                print(res_data)
                jsoninfo = json.loads(res_data)
                code = jsoninfo['status']['code']
                msg = jsoninfo['status']['msg']
                if "status" in jsoninfo and jsoninfo["status"]["code"] == 0:
                    result.append(
                        {"timestamp": current_time, "rec_length": rec_length, "result": jsoninfo, "file": filep})
                    res = self.parse_data(jsoninfo)
                    # self.dlog.logger.info('recognize_file.(time:{0}, title: {1})'.format(current_time, res[0]))
                    self.dlog.logger.info(
                        'recognize_file.(time:{0}, title: {1}, custom title: {2})'.format(current_time, res[0],
                                                                                          res[-2]))
                if code == 2005:
                    self.dlog.logger.warning('recognize_file.(time:{0}, code:{1}, Done!)'.format(current_time, code))
                    break
                elif code == 1001:
                    result.append(
                        {"timestamp": current_time, "rec_length": rec_length, "result": jsoninfo, "file": filep})
                    self.dlog.logger.info("recognize_file.(time:{0}, code:{1}, No_Result)".format(current_time, code))
                elif code == 3001:
                    self.dlog.logger.error(
                        'recognize_file.(time:{0}, code:{1}, Missing/Invalid Access Key)'.format(current_time, code))
                    break
                elif code == 3003:
                    self.dlog.logger.error(
                        'recognize_file.(time:{0}, code:{1}, Limit exceeded)'.format(current_time, code))
                elif code == 3000:
                    self.dlog.logger.error('recognize_file.(time:{0}, {1}, {2})'.format(current_time, code, msg))
                    self.write_error(filepath, i, 'NETWORK ERROR')
                i += step
            except Exception as e:
                self.dlog.logger.error('recognize_file.error', exc_info=True)
                self.write_error(filepath, i, 'JSON ERROR')
        return result

    def scan_file_main(self, option, start_time, stop_time):
        try:
            filepath = option.file_path
            step = option.step
            rec_length = option.rec_length
            with_duration = option.with_duration
            out_dir = option.out_dir
            if out_dir and not os.path.exists(out_dir):
                try:
                    os.makedirs(out_dir)
                except Exception as e:
                    self.dlog.logger.error("scan_file_main.create_out_dir_error:{0}, please check it!".format(out_dir),
                                           exc_info=True)
                    return

            file_type = option.file_type
            if start_time == 0 and stop_time == 0:
                file_total_seconds = int(ACRCloudRecognizer.get_duration_ms_by_file(filepath) / 1000)
                results = self.recognize_file(filepath, start_time, file_total_seconds, step, rec_length, with_duration)
            else:
                results = self.recognize_file(filepath, start_time, stop_time, step, rec_length, with_duration)

            filename_csv = 'result-' + os.path.basename(filepath.strip()) + '.csv'
            filename_xlsx = 'result-' + os.path.basename(filepath.strip()) + '.xlsx'
            filename_json = 'result-' + os.path.basename(filepath.strip()) + '.json'

            if results:
                if file_type == "csv":
                    self.export_to_csv(results, filename_csv, out_dir)
                elif file_type == "json":
                    self.export_to_json(results, filename_json, out_dir)
                else:
                    self.export_to_xlsx(results, filename_xlsx, out_dir)

            if with_duration == 1:
                new_results = []
                if results:
                    new_results = self.apply_filter(results)

                filename_with_duration_csv = 'result-' + os.path.basename(filepath.strip()) + '_with_duration.csv'
                filename_with_duration_xlsx = 'result-' + os.path.basename(filepath.strip()) + '_with_duration.xlsx'
                filename_with_duration_json = 'result-' + os.path.basename(filepath.strip()) + '_with_duration.json'

                if file_type == "csv":
                    self.export_to_csv(new_results, filename_with_duration_csv, out_dir)
                elif file_type == "json":

                    self.export_to_json(new_results, filename_with_duration_json, out_dir)
                else:
                    self.export_to_xlsx(new_results, filename_with_duration_xlsx, out_dir)
        except Exception as e:
            self.dlog.logger.error("scan_file_main.error", exc_info=True)
        return

    def scan_folder_main(self, option, start_time, stop_time):
        try:
            path = option.folder_path
            file_list = os.listdir(path)
            for i in file_list:
                option.file_path = path + '/' + i
                self.scan_file_main(option, start_time, stop_time)
        except Exception as e:
            self.dlog.logger.error("scan_folder_main.error", exc_info=True)


if __name__ == '__main__':
    usage = r'''
        _    ____ ____   ____ _                 _
       / \  / ___|  _ \ / ___| | ___  _   _  __| |
      / _ \| |   | |_) | |   | |/ _ \| | | |/ _` |
     / ___ \ |___|  _ <| |___| | (_) | |_| | (_| |
    /_/   \_\____|_| \_\\____|_|\___/ \____|\____|

    Usage:
    python acrcloud_scan_files_python.py -d folder_path
        python acrcloud_scan_files_python.py -f file_path
    Example:
        python acrcloud_scan_files_python.py -d ~/music
        python acrcloud_scan_files_python.py -f ~/testfiles/test.mp3
    If you want to change scan interval or you want to set recognize range,you can add some params
    Example:
        python acrcloud_scan_files_python.py -f ~/testfiles/test.mp3 -s 30 -r 0-20 -l 10
        python acrcloud_scan_files_python.py -d ~/music -s 30
    '''

    parser = optparse.OptionParser()
    parser.add_option('-f', '--file', dest='file_path', type='string', help='Scan file you want to recognize')
    parser.add_option('-c', '--config', dest='config', type='string', default="config.json", help='config file')
    parser.add_option('-d', '--folder', dest='folder_path', type='string', help='Scan folder you want to recognize')
    parser.add_option('-s', '--step', dest='step', type='int', default=10, help='step')
    parser.add_option('-l', '--rec_length', dest='rec_length', type='int', default=10, help='rec_length')
    parser.add_option('-e', '--error_file', dest='error_file', type='string', help='error scan file')
    parser.add_option('-r', '--range', dest='range', type='string', default='0-0', help='error scan file')
    parser.add_option('-w', '--with_duration', dest="with_duration", type='int', default=0, help='with_duration')
    parser.add_option('-o', '--out_dir', dest="out_dir", type='string', default="./", help='out_dir')
    parser.add_option('-t', '--file_type', dest="file_type", type='string', default="csv", help='file_type')

    (options, args) = parser.parse_args()
    start = int(options.range.split('-')[0])
    stop = int(options.range.split('-')[1])

    asf = ACRCloud_Scan_Files(options.config)
    if options.file_path:
        asf.empty_error_scan()
        asf.scan_file_main(options, start, stop)
    elif options.folder_path:
        asf.empty_error_scan()
        asf.scan_folder_main(options, start, stop)
    else:
        print(usage)
