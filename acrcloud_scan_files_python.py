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
    res = (current_time, title, artists, album,
           acrid, label, isrc, dezzer, spotify,
           itunes, youtube, custom_files_title, audio_id)
    return res


def recognize_file(filename, step):
    result = []
    i = 0
    retry = 3
    while True:
        filename, current_time, res_data = scan_file_part(filename, i)
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
        except:
            write_error(filename, i, 'JSON ERROR')
    return result


def main(target, step):
    results = recognize_file(target, step)
    filename = 'result-' + target.split('/')[-1].strip() + '.csv'
    if os.path.exists(filename):
        os.remove(filename)
    if results:
        with codecs.open(filename, 'w', 'utf-8-sig') as f:
            fields = ['time', 'title', 'artists', 'album', 'acrid', 'label', 'isrc', 'dezzer', 'spotify', 'itunes',
                      'youtube', 'custom_files_title', 'audio_id']
            dw = csv.writer(f)
            dw.writerow(fields)
            dw.writerows(results)


def path_main(path, step):
    file_list = os.listdir(path)
    for i in file_list:
        file_path = path + '/' + i
        main(file_path, step)


def empty_error_scan():
    if os.path.exists('error_scan.txt'):
        os.remove('error_scan.txt')


def scan_file_part(path, start_time):
    current_time = time.strftime('%H:%M:%S', time.gmtime(start_time))
    re = set_config()
    res_data = re.recognize_by_file(path, start_time)
    return path, current_time, res_data


def write_error(file_path, error_time, error_detail):
    with open('error_scan.txt', 'a',) as f:
        msg = file_path + '||' + str(error_time) + '||' + str(error_detail) + '\n'
        print msg
        f.write(msg)

if __name__ == '__main__':
    usage = '''
    Usage:
    python acrcloud_scan_files_python.py -d folder_path
        python acrcloud_scan_files_python.py -f file_path
    Example:
        python acrcloud_scan_files_python.py -d ~/music
        python acrcloud_scan_files_python.py -f ~/testfiles/test.mp3
    If you want to change scan interval,you can add step param
    Example:
        python acrcloud_scan_files_python.py -f ~/testfiles/test.mp3 -s 30
        python acrcloud_scan_files_python.py -d ~/music -s 30
    '''
    print usage
    parser = optparse.OptionParser()
    parser.add_option('-f', '--file', dest='file_name', type='string',
                      help='Scan file you want to recognize')
    parser.add_option('-d', '--folder', dest='folder', type='string',
                      help='Scan folder you want to recognize')
    parser.add_option('-s', '--step', dest='step', type='int', default=10,
                      help='step')
    (options, args) = parser.parse_args()
    if options.file_name:
        empty_error_scan()
        main(options.file_name, options.step)
    if options.folder:
        empty_error_scan()
        path_main(options.folder, options.step)
