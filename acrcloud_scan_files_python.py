#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import time
import json
import codecs
import optparse
import logging
from backports import csv
from acrcloud_filter import FilterWorker
from acrcloud_logger import AcrcloudLogger
from acrcloud.recognizer import ACRCloudRecognizer

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
        self.config_file = config_file
        self.init_log()
        self.init_config()

    def init_log(self):
        self.dlog = AcrcloudLogger('ACRCloud_ScanF', logging.INFO)
        if not self.dlog.addFilehandler(logfile = "log_scan_files.log", logdir = "./", loglevel = logging.WARN):
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
                self.dlog.logger.warn("init_config success!")
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
        with open('error_scan.txt', 'a',) as f:
            msg = file_path + '||' + str(error_time) + '||' + str(error_detail) + '\n'
            f.write(msg)

    def empty_error_scan(self):
        if os.path.exists('error_scan.txt'):
            os.remove('error_scan.txt')

    def parse_data(self, current_time, metadata):
        try:
            title, offset, isrc, upc, acrid, label, album = [""]*7
            artists, deezer, spotify, itunes, youtube, custom_files_title, audio_id  = [""]*7
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
        except Exception as e:
            self.dlog.logger.error("parse_data.error.data:{0}".format(metadata), exc_info=True)

        res = (current_time, title, artists, album, acrid, offset, label, isrc, upc,
                deezer, spotify, itunes, youtube, custom_files_title, audio_id)
        return res

    def do_recognize(self, filepath, start_time, rec_length):
        try:
            current_time = time.strftime('%d %H:%M:%S', time.gmtime(start_time))
            res_data = self.re_handler.recognize_by_file(filepath, start_time, rec_length)
            return filepath, current_time, res_data
        except Exception as e:
            self.dlog.logger.error("do_recognize.error.({0}, {1}, {})".format(filepath,start_time,rec_length),exc_info=True)
        return filepath, current_time, None

    def recognize_file(self, filepath, start_time, stop_time, step, rec_length, with_duration=0):
        self.dlog.logger.warn("scan_file.start_to_run: {0}".format(filepath))

        if with_duration == 1:
            self.dlog.logger.warn("results with duration...")
            fname = os.path.basename(filepath)
            fworker = FilterWorker("./", "result-"+fname+"_with_duration.csv")

        result = []
        for i in range(start_time, stop_time, step):
            filep, current_time, res_data = self.do_recognize(filepath, i, rec_length)
            try:
                ret_dict = json.loads(res_data)
                code = ret_dict['status']['code']
                msg = ret_dict['status']['msg']
                if 'metadata' in ret_dict:
                    metadata = ret_dict['metadata']
                    res = self.parse_data(current_time, metadata)
                    result.append(res)
                    if with_duration == 1:
                        fworker.do_filter(fname, ret_dict, rec_length, current_time)
                    self.dlog.logger.info('recognize_file.(time:{0}, title: {1})'.format(current_time, res[1]))
                if code == 2005:
                    self.dlog.logger.warn('recognize_file.(time:{0}, Done!)'.format(current_time, code))
                    break
                elif code == 1001:
                    self.dlog.logger.info("recognize_file.(time:{0}, No_Result)".format(current_time, code))
                    if with_duration == 1:
                        fworker.do_filter(fname, ret_dict, rec_length, current_time)
                elif code == 3001:
                    self.dlog.logger.error('recognize_file.(time:{0}, Missing/Invalid Access Key)'.format(current_time, code))
                    break
                elif code == 3003:
                    self.dlog.logger.error('recognize_file.(time:{0}, Limit exceeded)'.format(current_time, code))
                elif code == 3000:
                    self.dlog.logger.error('recognize_file.(time:{0}, {1}, {2})'.format(current_time, code, msg))
                    self.write_error(filename, i, 'NETWORK ERROR')
                i += step
            except Exception as e:
                self.dlog.logger.error('recognize_file.error', exc_info=True)
                self.write_error(filepath, i, 'JSON ERROR')
        if with_duration == 1:
            fworker.end_filter(fname, rec_length, current_time)
        return result


    def scan_file_main(self, option, start_time, stop_time):
        try:
            filepath = option.file_path
            step = option.step
            rec_length = option.rec_length
            with_duration = option.with_duration
            if start_time == 0 and stop_time == 0:
                file_total_seconds =  int(ACRCloudRecognizer.get_duration_ms_by_file(filepath)/1000)
                results = self.recognize_file(filepath, start_time, file_total_seconds, step, rec_length, with_duration)
            else:
                results = self.recognize_file(filepath, start_time, stop_time, step, rec_length, with_duration)

            filename = 'result-' + os.path.basename(filepath.strip()) + '.csv'
            if os.path.exists(filename):
                os.remove(filename)
            if results:
                with codecs.open(filename, 'w', 'utf-8-sig') as f:
                    fields = ['time', 'title', 'artists', 'album', 'acrid', 'play offset(ms)', 'label', 'isrc', 'upc',
                              'dezzer', 'spotify', 'itunes', 'youtube', 'custom_files_title', 'audio_id']
                    dw = csv.writer(f)
                    dw.writerow(fields)
                    dw.writerows(results)
        except Exception as e:
            self.dlog.logger.error("scan_file_main.error", exc_info=True)


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
