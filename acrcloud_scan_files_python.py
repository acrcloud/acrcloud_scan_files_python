#!/usr/bin/env python
# encoding:utf-8

import os
import codecs
import sys
import json
from acrcloudpysdk.recognizer import ACRCloudRecognizer
import time
from backports import csv
import getopt


step = 10


def get_tracks_artists(artists):
    artists_namelist = []
    for artist in artists:
        artists_namelist.append(artist['name'])
    space = ','
    artists_names = space.join(artists_namelist)
    return artists_names


def recognize_music(filename):
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
    result = []
    i = 0
    retry = 3
    while True:
        current_time = time.strftime('%H:%M:%S', time.gmtime(i))
        res_data = re.recognize_by_file(filename, i)
        if res_data == -1:
            retry -= 1
        if retry > 0:
            try:
                ret_dict = json.loads(res_data)
                code = ret_dict['status']['code']
                if code == 0:
                    metadata = ret_dict['metadata']
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
                        custom_files_title = metadata['custom_files'][0]['title']
                    except:
                        custom_files_title = ''
                    try:
                        audio_id = metadata['custom_files'][0]['audio_id']
                    except:
                        audio_id = ''
                    res = (current_time, title, artists, album,
                           acrid, label, isrc, dezzer, spotify,
                           itunes, custom_files_title, audio_id)
                    print current_time, res
                    result.append(res)
                elif code == 1001:
                    print "No Result"
                elif code == 3001:
                    print 'Missing/Invalid Access Key'
                    break
                elif code == 3003:
                    print 'Limit exceeded'
                    return result
            except:
                pass
        else:
            break
        i += step
    return result


def save_results(target):
    try:
        results = recognize_music(target)
        filename = 'result-' + target.split('/')[-1].strip() + '.csv'
        try:
            os.remove(filename)
        except:
            pass
        if results:
            with codecs.open(filename, 'w', 'utf-8-sig') as f:
                fields = ['time', 'title', 'artists', 'album', 'acrid', 'isrc', 'dezzer', 'spotify', 'itunes', 'custom_files_title', 'audio_id']
                dw = csv.writer(f)
                dw.writerow(fields)
                dw.writerows(results)
    except:
        pass


def usage():
    print '[-] Usage: acrcloud_scan_files_python.py target'
    print '[-] -d folder path'
    print '[-] -f file path'
    print '[-] -h get usage help'
    print '[-] Scan Folder Example: python acrcloud_scan_files_python.py -d ~/music'
    print '[-] Scan File Example: python acrcloud_scan_files_python.py -f ~/testfiles/test.mp3'


def path_main(path):
    file_list = os.listdir(path)
    for file in file_list:
        filepath = path + '/' + file
        save_results(filepath)

os.getcwd()
if __name__ == '__main__':
    try:
        usage()
        opts, args = getopt.getopt(sys.argv[1:], "hd:f:")
    except getopt.GetoptError, err:
        print str(err)
        sys.exit()
    for op, value in opts:
        if op == '-h':
            usage()
            sys.exit()
        elif op == '-d':
            path = value
            path_main(value)
        elif op == '-f':
            file_path = value
            save_results(file_path)
