#!/usr/bin/env python
# coding:utf-8

import os
import codecs
import json
from acrcloudpysdk.recognizer import ACRCloudRecognizer
import time
from backports import csv
import optparse


def get_tracks_artists(artists):
    artists_namelist = []
    for artist in artists:
        artists_namelist.append(artist['name'])
    space = ','
    artists_names = space.join(artists_namelist)
    return artists_names


def set_config():
    with codecs.open('config.json', 'r') as f:
        json_config = json.loads(f.read())
        host = json_config['host']
        key = json_config['access_key']
        secret = json_config['access_secret']

    config = {
        'host': str(host),
        'access_key': str(key),
        'access_secret': str(secret),
        'debug': False,
        'timeout': 10  # seconds
    }
    re = ACRCloudRecognizer(config)
    return re


def parse_data(current_time, metadata):
    try:
        title = metadata['music'][0]['title']
    except:
        title = ''
    try:
        offset = metadata['music'][0]['play_offset_ms']
    except:
        offset = ''
    try:
        isrc = metadata['music'][0]['external_ids']['isrc']
    except:
        isrc = ''
    try:
        acrid = metadata['music'][0]['acrid']
    except:
        acrid = ''
    try:
        label = metadata['music'][0]['label']
    except:
        label = ''
    try:
        album = metadata['music'][0]['album']['name']
    except:
        album = ''
    try:
        artists = get_tracks_artists(metadata['music'][0]['artists'])
    except:
        artists = ''
    try:
        dezzer = str(metadata['music'][0]['external_metadata']['deezer']['track']['id'])
    except:
        dezzer = ''
    try:
        spotify = str(metadata['music'][0]['external_metadata']['spotify']['track']['id'])
    except:
        spotify = ''
    try:
        itunes = str(metadata['music'][0]['external_metadata']['itunes']['track']['id'])
    except:
        itunes = ''
    try:
        youtube = metadata['music'][0]['external_metadata']['youtube']['vid']
    except:
        youtube = ''
    try:
        custom_files_title = metadata['custom_files'][0]['title']
    except:
        custom_files_title = ''
    try:
        audio_id = metadata['custom_files'][0]['audio_id']
    except:
        audio_id = ''
    res = (current_time, title, artists, album, acrid,
           offset, label, isrc, dezzer, spotify, itunes,
           youtube, custom_files_title, audio_id)
    return res


def recognize_file(filename,  start_time, stop_time, step, rec_length):
    result = []
    for i in range(start_time, stop_time, step):
        filename, current_time, res_data = scan_file_part(filename, i, rec_length)
        print filename, current_time
        try:
            ret_dict = json.loads(res_data)
            code = ret_dict['status']['code']
            msg = ret_dict['status']['msg']
            if 'metadata' in ret_dict:
                metadata = ret_dict['metadata']
                res = parse_data(current_time, metadata)
                result.append(res)
                print res[1]
            if code == 2005:
                print 'done!'
                break
            elif code == 1001:
                print "No Result"
            elif code == 3001:
                print 'Missing/Invalid Access Key'
                break
            elif code == 3003:
                print 'Limit exceeded'
            elif code == 3000:
                print msg
                write_error(filename, i, 'NETWORK ERROR')
            i += step
        except Exception as e:
            print str(e)
            write_error(filename, i, 'JSON ERROR')
    return result


def scan_file_main(option, start_time, stop_time):
    target = option.file_path
    step = option.step
    rec_length = option.rec_length
    if start_time == 0 and stop_time == 0:
        results = recognize_file(target, start_time, ACRCloudRecognizer.get_duration_ms_by_file(target), step, rec_length)
    else:
        results = recognize_file(target, start_time, stop_time, step)
    filename = 'result-' + target.split('/')[-1].strip() + '.csv'
    if os.path.exists(filename):
        os.remove(filename)
    if results:
        with codecs.open(filename, 'w', 'utf-8-sig') as f:
            fields = ['time', 'title', 'artists', 'album', 'acrid', 'play offset(ms)', 'label', 'isrc', 'dezzer',
                      'spotify', 'itunes', 'youtube', 'custom_files_title', 'audio_id']
            dw = csv.writer(f)
            dw.writerow(fields)
            dw.writerows(results)


def scan_folder_main(option, start_time, stop_time):
    path = option.folder_path
    step = option.step

    file_list = os.listdir(path)
    for i in file_list:
        option.file_path = path + '/' + i
        scan_file_main(option, start_time, stop_time)


def empty_error_scan():
    if os.path.exists('error_scan.txt'):
        os.remove('error_scan.txt')


def scan_file_part(path, start_time, rec_length):
    current_time = time.strftime('%H:%M:%S', time.gmtime(start_time))
    re = set_config()
    res_data = re.recognize_by_file(path, start_time, rec_length)
    return path, current_time, res_data


def write_error(file_path, error_time, error_detail):
    with open('error_scan.txt', 'a',) as f:
        msg = file_path + '||' + str(error_time) + '||' + str(error_detail) + '\n'
        print msg
        f.write(msg)


def scan_txt_file(file_path):
    with codecs.open(file_path, 'r', 'utf-8') as f:
        tasks = f.readlines(file_path)
    for task in tasks:
        result = []
        error_task = task.split('||')
        task_file, task_time = error_task[0].encode('utf-8'), int(error_task[1])
        path, current_time, res_data = scan_file_part(task_file, task_time)
        result_file_name = 'result-error_scan.csv'
        print file_path, current_time
        try:
            ret_dict = json.loads(res_data)
            code = ret_dict['status']['code']
            msg = ret_dict['status']['msg']
            if 'metadata' in ret_dict:
                metadata = ret_dict['metadata']
                res = parse_data(current_time, metadata)
                result.append(res)
                if result:
                    with codecs.open(result_file_name, 'a', 'utf-8-sig') as f:
                        dw = csv.writer(f)
                        dw.writerows(result)
                print res[1]
            if code == 2005:
                print 'done!'
                break
            elif code == 1001:
                print "No Result"
            elif code == 3001:
                print 'Missing/Invalid Access Key'
                break
            elif code == 3003:
                print 'Limit exceeded'
            elif code == 3000:
                print msg
        except Exception as e:
            print str(e)


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
    parser.add_option('-f', '--file', dest='file_path', type='string',
                      help='Scan file you want to recognize')
    parser.add_option('-d', '--folder', dest='folder_path', type='string',
                      help='Scan folder you want to recognize')
    parser.add_option('-s', '--step', dest='step', type='int', default=10,
                      help='step')
    parser.add_option('-l', '--rec_length', dest='rec_length', type='int', default=10,
                      help='rec_length')
    parser.add_option('-e', '--error_file', dest='error_file', type='string',
                      help='error scan file')
    parser.add_option('-r', '--range', dest='range', type='string', default='0-0',
                      help='error scan file')
    (options, args) = parser.parse_args()
    start = int(options.range.split('-')[0])
    stop = int(options.range.split('-')[1])
    if options.file_path:
        empty_error_scan()
        scan_file_main(options, start, stop)
    elif options.folder_path:
        empty_error_scan()
        scan_folder_main(options, start, stop)
    elif options.error_file:
        scan_txt_file(options.error_file)
    else:
        print usage
