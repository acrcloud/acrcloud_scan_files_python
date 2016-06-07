#!/usr/bin/env python
# coding:utf-8

import os
import codecs
import sys
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


def recognize_music(filename, step):
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
        print filename, current_time
        code = json.loads(res_data)['status']['code']
        if code == 3000:
            retry -= 1
            if retry == 0:
                print "Please Check Your Network!"
        if code == 2005:
            break
        if retry > 0:
            try:
                ret_dict = json.loads(res_data)
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
                    result.append(res)
                    print res[1]
                elif code == 1001:
                    print "No Result"
                elif code == 3001:
                    print 'Missing/Invalid Access Key'
                    break
                elif code == 3003:
                    print 'Limit exceeded'
            except:
                pass
        else:
            retry = 3
        i += step
    return result


def main(target, step):
    try:
        results = recognize_music(target, step)
        filename = 'result-' + target.split('/')[-1].strip() + '.csv'
        try:
            os.remove(filename)
        except:
            pass
        if results:
            with codecs.open(filename, 'w', 'utf-8-sig') as f:
                fields = ['time', 'title', 'artists', 'album', 'acrid', 'label', 'isrc', 'dezzer', 'spotify', 'itunes', 'youtube', 'custom_files_title', 'audio_id']
                dw = csv.writer(f)
                dw.writerow(fields)
                dw.writerows(results)
    except:
        pass


def path_main(path, step):
    file_list = os.listdir(path)
    for i in file_list:
        file_path = path + '/' + i
        main(file_path, step)

if __name__ == '__main__':
    usage = '''
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
        main(options.file_name, options.step)
    if options.folder:
        path_main(options.folder, options.step)



