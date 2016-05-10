#!/usr/bin/env python
# encoding:utf-8

import os
import codecs
import sys
import json
from acrcloudpysdk.recognizer import ACRCloudRecognizer
import time
from backports import csv
from multiprocessing import Pool, cpu_count

step = 10


def get_tracks_artists(artists):
    artists_namelist = []
    for artist in artists:
        artists_namelist.append(artist['name'])
    space = ','
    artists_names = space.join(artists_namelist)
    return artists_names


def recognize_music(filename):
    global ret_dict
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
        print res_data
        print current_time
        if res_data == -1:
            retry -= 1
        if retry > 0:
            try:
                print res_data
                ret_dict = json.loads(res_data)
            except:
                ret_dict['status']['msg'] = 'Error'
            if ret_dict['status']['msg'] == 'Success':
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
                result.append(res)

            i += step
        else:
            return result

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
                fields = ['time', 'title', 'artists', 'album', 'acrid', 'isrc', 'dezzer', 'spotify', 'itunes']
                dw = csv.writer(f)
                dw.writerow(fields)
                dw.writerows(results)
    except:
        pass


def main():
    p = Pool(cpu_count())
    path = os.getcwd()
    file_list = os.listdir(path)
    p.map(save_results, file_list)
    p.close()
    p.join()


if __name__ == '__main__':
    if 1 != 1:
        print '[-] Usage: python recognize.py'
        print '[-] Put this python script to the file you want to recognize'
        sys.exit()
    else:
        main()
