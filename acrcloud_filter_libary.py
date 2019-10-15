#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import json
import copy
import math
import datetime
import traceback
import tools_str_sim
import acrcloud_logger
from dateutil.relativedelta import *

if sys.version_info.major == 2:
    reload(sys)
    sys.setdefaultencoding("utf8")

NORESULT = "noResult"

class ResultFilter:

    def __init__(self, dlog):
        self._dlog = dlog
        self._real_music = {}
        self._real_music_list_num = 3
        self._real_custom = {}
        self._real_custom_list_num = 3
        self._real_custom_valid_interval = 5*60
        self._delay_music = {}
        self._delay_music_last_result = {}
        self._delay_music_interval_threshold = 2*60
        self._delay_custom = {}
        self._delay_custom_played_duration_min = 2
        self._delay_list_max_num = 35
        self._delay_list_threshold = 120

    def get_mutil_result_title(self, data, itype='music', isize = 1):
        ret_list = []
        index = 0
        json_res = data["result"]
        if json_res == NORESULT:
            return [NORESULT]
        try:
            if json_res['status']['code'] == 0:
                if itype == 'music':
                    if 'metadata' in json_res and 'music' in json_res['metadata']:
                        for item in json_res['metadata']['music']:
                            ret_list.append(item['title'])
                            index += 1
                            if index >= isize:
                                break
                    elif 'metainfos' in json_res:
                        for item in json_res['metainfos']:
                            ret_list.append(item['title'])
                            index += 1
                            if index >= isize:
                                break
                elif itype == 'custom':
                    if 'metadata' in json_res and 'custom_files' in json_res['metadata']:
                        for item in json_res['metadata']['custom_files']:
                            ret_list.append(item['title'])
                            index += 1
                            if index >= isize:
                                break
        except Exception as e:
            self._dlog.logger.error("Error@get_mutil_result_title", exc_info=True)
            self._dlog.logger.error("Error_Data: {0}".format(data))
        return ret_list if ret_list else [NORESULT]

    def get_mutil_result_acrid(self, data, itype='music', isize = 1):
        ret_list = []
        index = 0
        json_res = data["result"]
        if json_res == NORESULT:
            return [NORESULT]
        try:
            if json_res['status']['code'] == 0:
                if itype == 'music':
                    if 'metadata' in json_res and 'music' in json_res['metadata']:
                        for item in json_res['metadata']['music']:
                            ret_list.append(item['acrid'])
                            index += 1
                            if index >= isize:
                                break
                    elif 'metainfos' in json_res:
                        for item in json_res['metainfos']:
                            ret_list.append(item['acrid'])
                            index += 1
                            if index >= isize:
                                break
                elif itype == 'custom':
                    if 'metadata' in json_res and 'custom_files' in json_res['metadata']:
                        for item in json_res['metadata']['custom_files']:
                            ret_list.append(item['acrid'])
                            index += 1
                            if index >= isize:
                                break
        except Exception as e:
            self._dlog.logger.error("Error@get_mutil_result_acrid", exc_info=True)
            self._dlog.logger.error("Error_Data: {0}".format(json.dumps(result)))
        return ret_list if ret_list else [NORESULT]

    def swap_position(self, ret_title, ret_data, itype):
        json_res = ret_data["result"]
        meta_type = None
        music_list = []
        if itype == 'music':
            if 'metadata' in json_res:
                music_list = json_res['metadata']['music']
            elif 'metainfos' in json_res:
                music_list = json_res['metainfos']
        elif itype == 'custom':
            music_list = json_res['metadata']['custom_files']

        if music_list:
            ret_index = 0
            for index, item in enumerate(music_list):
                if itype == "music":
                    if item['title'] == ret_title:
                        ret_index = index
                        break
                else:
                    if item['acrid'] == ret_title:
                        ret_index = index
                        break
            if ret_index > 0:
                music_list[0], music_list[ret_index] = music_list[ret_index], music_list[0]

    def custom_result_append(self, ret_data, title, from_data, count, tmp_deal_title_map):
        ret_title_set = set()
        for item in ret_data['result']['metadata']['custom_files']:
            ret_title_set.add(item['acrid'])

        for item in from_data['result']['metadata']['custom_files']:
            acrid = item['acrid']
            if acrid == title and acrid not in ret_title_set:
                item['count'] = count
                ret_data['result']['metadata']['custom_files'].append(item)
                ret_title_set.add(acrid)

        for item in from_data['result']['metadata']['custom_files']:
            acrid = item['acrid']
            if acrid not in ret_title_set:
                if acrid in tmp_deal_title_map:
                    item['count'] = tmp_deal_title_map[acrid]['count']
                    ret_data['result']['metadata']['custom_files'].append(item)

    def get_play_offset(self, data, itype='music'):
        try:
            play_offset_ms = 0
            result = data['result']
            if result['status']['code'] == 1001:
                return 0
            if itype == 'music':
                play_offset_ms = result['metadata']['music'][0]['play_offset_ms']
            elif itype == 'custom':
                play_offset_ms = result['metadata']['custom_files'][0]['play_offset_ms']
        except Exception as e:
            self._dlog.logger.error("Error@Get_Play_Offset, error_data: {0}, {1}".format(itype, data), exc_info=True)
        return play_offset_ms/1000.0

    def get_db_play_offset(self, data, offset_type="begin", itype='music'):
        """
        itype : music or custom
        offset_type : begin or end offset
        """
        try:
            if offset_type not in ['begin', 'end']:
                self._dlog.logger.error("Error@Get_DB_Play_Offset.offset_type({0}) error".format(offset_type))
                return (None, self.get_play_offset(data, itype)) #if offset_type error, return play_offset_ms

            db_offset_key = "db_{0}_time_offset_ms".format(offset_type)
            sample_offset_key = "sample_{0}_time_offset_ms".format(offset_type)

            db_play_offset_ms = 0 #ms
            sample_play_offset_ms = 0
            result = data['result']
            if result['status']['code'] == 1001:
                return 0
            if itype == 'music':
                db_play_offset_ms = result['metadata']['music'][0][db_offset_key]
                sample_play_offset_ms = result['metadata']['music'][0][sample_offset_key]
            elif itype == 'custom':
                db_play_offset_ms = result['metadata']['custom_files'][0][db_offset_key]
                sample_play_offset_ms = result['metadata']['custom_files'][0][sample_offset_key]

            return (int(sample_play_offset_ms)/1000.0, int(db_play_offset_ms)/1000.0)
        except Exception as e:
            self._dlog.logger.error("Error@please contact support@acrcloud.com to add offset config for your access_key")
        return (None, None)

    def get_duration(self, end_timestamp, start_timestamp):
        end = datetime.datetime.strptime(end_timestamp, '%H:%M:%S')
        start = datetime.datetime.strptime(start_timestamp, '%H:%M:%S')
        return (end - start).total_seconds()

    def get_duration_accurate(self, end_data, start_data, itype='music'):
        monitor_len = end_data.get('rec_length', 10)
        end_play_offset = self.get_play_offset(end_data, itype)
        start_play_offset = self.get_play_offset(start_data, itype)
        pre_seconds = max(20, monitor_len*2)
        if int(start_play_offset) < pre_seconds:
            start_play_offset = 0
        else:
            start_play_offset = start_play_offset - (monitor_len/2)
        return int(round(end_play_offset - start_play_offset))

    def get_duration_accurate_use_db_offset(self, end_data, begin_data, isize, itype='music'):
        begin_timestamp = datetime.datetime.strptime(begin_data['timestamp'], "%H:%M:%S")

        monitor_len = end_data.get('rec_length', 10)

        end_sample_offset, end_db_offset = self.get_db_play_offset(end_data, 'end', itype)
        begin_sample_offset, begin_db_offset = self.get_db_play_offset(begin_data, 'begin', itype)
        for i in [ end_sample_offset, end_db_offset, begin_sample_offset, begin_db_offset]:
            if i is None:
                return 0, 0, 0, begin_data["timestamp"]

        accurate_begin_timestamp = (begin_timestamp + relativedelta(seconds=int(float(begin_sample_offset)))).strftime("%H:%M:%S")

        db_len = int(round(end_db_offset - begin_db_offset))
        sample_len = int(round(end_sample_offset - begin_sample_offset + (isize-1)*monitor_len))

        mix_len = 0
        if int(begin_sample_offset) == 0 and int(begin_db_offset) == 0:
            mix_len = (isize-1)*monitor_len + end_sample_offset
        elif int(begin_sample_offset) == 0:
            if begin_db_offset <= monitor_len:
                mix_len = (isize-1)*monitor_len + end_sample_offset
            else:
                mix_len = (isize-1)*monitor_len + end_sample_offset - begin_sample_offset
        elif int(begin_db_offset) == 0:
            mix_len = (isize-1)*monitor_len + end_sample_offset - begin_sample_offset
        else:
            mix_len = (isize-1)*monitor_len + end_sample_offset - begin_sample_offset
        mix_len = int(round(mix_len))

        return sample_len, db_len, mix_len, accurate_begin_timestamp

    def judge_zero_item_contain_current_result(self, ret_sim_title, zero_data, itype="music"):
        """
        itype: music => title is track name
        itype: custom => title is acrid
        """
        try:
            is_contain = False
            if itype == "music":
                zero_title_list = self.get_mutil_result_title(zero_data, 'music', 5)
            elif itype == "custom":
                zero_title_list = self.get_mutil_result_acrid(zero_data, 'custom', 5)
            else:
                return is_contain

            for ztitle in zero_title_list:
                if ztitle == NORESULT:
                    break
                sim_zero_title = self.tryStrSub(ztitle)[0] if itype == "music" else ztitle
                if sim_zero_title == ret_sim_title:
                    is_contain = True
                    self.swap_position(ztitle, zero_data, itype)
                    break
        except Exception as e:
            self._dlog.logger.error("Error@judge_zero_item_contain_current_result", exc_info=True)
        return is_contain

    def judge_latter_item_contain_current_result(self, ret_sim_title, latter_data, itype="music"):
        """
        itype: music => title is track name
        itype: custom => title is acrid
        """
        try:
            is_contain = False
            latter_data_swaped = None
            if itype == "music":
                latter_title_list = self.get_mutil_result_title(latter_data, 'music', 5)
            elif itype == "custom":
                latter_title_list = self.get_mutil_result_acrid(latter_data, 'custom', 5)
            else:
                return is_contain, latter_data_swaped

            for ltitle in latter_title_list:
                if ltitle == NORESULT:
                    break
                sim_latter_title = self.tryStrSub(ltitle)[0] if itype == "music" else ltitle
                if sim_latter_title == ret_sim_title:
                    is_contain = True
                    latter_data_swaped = copy.deepcopy(latter_data)
                    self.swap_position(ltitle, latter_data_swaped, itype)
                    break
        except Exception as e:
            self._dlog.logger.error("Error@judge_latter_item_contain_current_result", exc_info=True)
        return is_contain, latter_data_swaped

    def real_check_title_custom(self, stream_id, title, timestamp_obj):
        now_timestamp = timestamp_obj #datetime.datetime.utcnow()
        if stream_id not in self._real_custom:
            self._real_custom[stream_id] = [[('','')], '']

        if len(self._real_custom[stream_id][0]) > self._real_custom_list_num:
            self._real_custom[stream_id][0] = self._real_custom[stream_id][0][-self._real_custom_list_num:]
            his_list_num = self._real_custom_list_num
        else:
            his_list_num = len(self._real_custom[stream_id][0])

        for i in range(his_list_num-1, -1, -1):
            if self._real_custom[stream_id][0][i][0] == title:
                his_timestamp = self._real_custom[stream_id][0][i][1]
                his_time_obj = datetime.datetime.strptime(his_timestamp, '%H:%M:%S')
                if (now_timestamp - his_time_obj).total_seconds() <= self._real_custom_valid_interval:
                    return True
            if title == NORESULT:
                break

        return False

    def checkResultSim(self, idx, curr_title, his_title, stream_id):
        if not curr_title or not his_title:
            return False
        sim, detail = tools_str_sim.str_sim(curr_title, his_title)
        if not sim and curr_title != NORESULT and his_title != NORESULT:
            pass
        return sim

    def checkSame(self, curr_title, stream_id):
        self._real_music[stream_id] = self._real_music.get(stream_id, [[''], ''])
        if len(self._real_music[stream_id][0]) > self._real_music_list_num:
            self._real_music[stream_id][0] = self._real_music[stream_id][0][-self._real_music_list_num:]
            his_max = self._real_music_list_num
        else:
            his_max = len(self._real_music[stream_id][0])
        for i in range(his_max-1, -1, -1):
            if self.checkResultSim(i, curr_title, self._real_music[stream_id][0][i], stream_id):
                return True
            if curr_title == NORESULT:
                break
        return False

    def updateResultTitle(self, data, new_title):
        if new_title == NORESULT:
            return
        try:
            json_res = data["result"]
            metainfos = json_res.get("metainfos")
            metadata = json_res.get("metadata")
            if metainfos:
                metainfos[0]['title'] = new_title
            else:
                if metadata.get('music'):
                    metadata['music'][0]['title'] = new_title
                else:
                    metadata['custom_files'][0]['title'] = new_title
        except Exception as e:
            self._dlog.logger.error("Error@updateResultTitle", exc_info=True)

    def tryStrSub(self, try_str):
        sub_str = tools_str_sim.str_sub(try_str)
        if len(sub_str) > 0 and len(try_str) > len(sub_str):
            return sub_str, True
        return try_str, False

    def tryUpdateResultTitle(self, data, itype):
        if itype == 'custom':
            title = self.get_mutil_result_title(data, 'custom', 1)[0]
            return title
        title = self.get_mutil_result_title(data, 'music', 1)[0]
        stream_id = data.get("stream_id")
        new_title, try_status = self.tryStrSub(title)
        if try_status:
            self.updateResultTitle(data, new_title)
            return new_title
        return title

    def deal_real_history(self, data):
        is_new = False
        result = None
        curr_title = self.get_mutil_result_title(data, 'music', 1)[0]
        stream_id = data.get("stream_id")
        if not stream_id:
            return result, is_new
        if curr_title == NORESULT:
            if not self.checkSame(curr_title, stream_id):
                self._real_music[stream_id][0].append(curr_title)
                self._real_music[stream_id][1] = data
                result = data
                is_new = True
            else:
                result = None
                is_new = False
        else:
            if self.checkSame(curr_title, stream_id):
                result = self._real_music[stream_id][1]
                is_new = False
            else:
                self._real_music[stream_id][0].append(curr_title)
                self._real_music[stream_id][1] = data
                result = data
                is_new = True

        return result, is_new

    def deal_delay_history(self, data):
        stream_id = data.get("stream_id")
        timestamp = data.get("timestamp")
        raw_title = self.get_mutil_result_title(data, 'music', 1)[0]
        sim_title = self.tryStrSub(raw_title)
        if stream_id not in self._delay_music:
            self._delay_music[stream_id] = [(raw_title, sim_title[0], timestamp, data)]
        else:
            self._delay_music[stream_id].append((raw_title, sim_title[0], timestamp, data))

        if len(self._delay_music[stream_id]) > self._delay_list_max_num :
            return self.runDelayX_for_music_delay2(stream_id)
        else:
            return None

    def compute_played_duration(self, history_data, start_index, end_index, judge_zero_or_latter=True, itype="music"):
        retdata = history_data[start_index][-1]

        if itype == "music":
            ret_title = self.get_mutil_result_title(retdata, 'music', 1)[0]
            ret_sim_title = history_data[start_index][1]
        elif itype == "custom":
            ret_title = self.get_mutil_result_acrid(retdata, 'custom', 1)[0]
            ret_sim_title = ret_title

        if judge_zero_or_latter and start_index == 1:
            if self.judge_zero_item_contain_current_result(ret_sim_title, history_data[0][-1], itype):
                start_index = 0

        is_contain = False
        latter_data_swaped = None
        if judge_zero_or_latter and (end_index + 1 <= len(history_data) - 1):
            is_contain, latter_data_swaped = self.judge_latter_item_contain_current_result(ret_sim_title, history_data[end_index+1][-1], itype)

        if itype == "music":
            start_timestamp = history_data[start_index][2]
            end_timestamp = history_data[end_index][2]
            start_data = history_data[start_index][3]
            end_data = history_data[end_index][3]
        else:
            start_timestamp = history_data[start_index][1]
            end_timestamp = history_data[end_index][1]
            start_data = history_data[start_index][2]
            end_data = history_data[end_index][2]

        duration = self.get_duration(end_timestamp, start_timestamp)
        duration_accurate = self.get_duration_accurate(end_data, start_data, itype)
        isize = end_index - start_index + 1
        if is_contain:
            end_data = latter_data_swaped
            isize += 1

        sample_duraion, db_duration, mix_duration, accurate_timestamp_utc = self.get_duration_accurate_use_db_offset(end_data, start_data, isize, itype)

        ret_dict = {
            "duration" : duration,
            "duration_accurate" : duration_accurate,
            "sample_duration" : sample_duraion,
            "db_duration" : db_duration,
            "mix_duration" : mix_duration,
            "accurate_timestamp_utc" : accurate_timestamp_utc,
        }
        return ret_dict

    def get_data_duration_ms(self, data):
        try:
            duration_ms = -1
            json_res = data["result"]
            if json_res['status']['code'] == 0:
                if 'metadata' in json_res and 'music' in json_res['metadata']:
                    if len(json_res['metadata']['music']) > 0:
                        duration_ms = json_res["metadata"]["music"][0]["duration_ms"]
        except Exception as e:
            self._dlog.logger.error("Error@get_data_duration_ms", exc_info=True)
        return (duration_ms/1000.0) if duration_ms != -1 else duration_ms

    def get_time_diff(self, start_timestamp, end_timestamp, tformat="%Y-%m-%d %H:%M:%S"):
        try:
            diff_sec = 0
            start_obj = datetime.datetime.strptime(start_timestamp, tformat)
            end_obj = datetime.datetime.strptime(end_timestamp, tformat)
            diff_sec = int((end_obj - start_obj).total_seconds())
        except Exception as e:
            self._dlog.logger.error("Error@get_diff_seconds", exc_info=True)
        return diff_sec

    def remove_next_result_from_now_result_list_for_music_delay2(self, history_data, ret_data, max_index):
        #Just for music delay2 filter
        try:
            if ret_data and len(history_data) >= max_index+2:
                raw_title, sim_title, timestamp, next_data = history_data[max_index + 1]
                if next_data:
                    next_title_list = self.get_mutil_result_title(next_data, 'music', 1)
                    next_title_set = set(next_title_list)
                    new_ret_music = []
                    for index, item in enumerate(ret_data["result"]["metadata"]["music"]):
                        if index == 0 or (item["title"] not in next_title_set):
                            new_ret_music.append(item)
                    ret_data["result"]["metadata"]["music"] = new_ret_music
        except Exception as e:
            self._dlog.logger.error("Error@remove_next_result_from_now_result_list_for_music_delay2", exc_info=True)

    def result_append_for_music_delay2(self, ret_data, title, from_data):
        try:
            ret_title_set = set()
            for item in ret_data['result']['metadata']['music']:
                sim_title = self.tryStrSub(item['title'])[0]
                ret_title_set.add(sim_title)

            for item in from_data['result']['metadata']['music']:
                from_title = item['title']
                sim_from_title = self.tryStrSub(from_title)[0]
                if sim_from_title == title and sim_from_title not in ret_title_set:
                    ret_data['result']['metadata']['music'].append(item)
                    ret_title_set.add(sim_from_title)
        except Exception as e:
            self._dlog.logger.error("Error@result_append_for_music_delay2", exc_info=True)

    def get_custom_duration_by_title(self, title, ret_data):
        try:
            duration = 0
            db_end_offset = 0
            for index, item in enumerate(ret_data["result"]["metadata"]["custom_files"]):
                #custom 获取的title是acrid
                if title == item["acrid"]:
                    duration_ms = int(item["duration_ms"])
                    db_end_offset_ms = int(item["db_end_time_offset_ms"])
                    if duration_ms >= 0:
                        duration = int(duration_ms/1000)
                    if db_end_offset_ms:
                        db_end_offset = int(db_end_offset_ms/1000)
        except Exception as e:
            self._dlog.logger.error("Error@get_custom_duration_by_title, error_data:{0}".format(ret_data), exc_info=True)
        return duration, db_end_offset

    def get_music_duration_by_title(self, title, ret_data):
        try:
            duration = 0
            db_end_offset = 0
            if "metadata" in ret_data["result"] and "music" in ret_data["result"]["metadata"]:
                for index, item in enumerate(ret_data["result"]["metadata"]["music"]):
                    if title == item["title"]:
                        duration_ms = int(item["duration_ms"])
                        db_end_offset_ms = int(item["db_end_time_offset_ms"])
                        if duration_ms >= 0:
                            duration = int(duration_ms/1000)
                        if db_end_offset_ms:
                            db_end_offset = int(db_end_offset_ms/1000)
        except Exception as e:
            self._dlog.logger.error("Error@get_custom_duration_by_title, error_data:{0}".format(ret_data), exc_info=True)
        return duration, db_end_offset

    def delay_dynamic_judge_size(self, deal_title_map, history_data, itype):
        try:
            judge_size = 5
            if itype == "custom":
                title = sorted(deal_title_map.items(), key=lambda x:x[1]["score"], reverse=True)[0][0]
            else:
                title = deal_title_map.keys()[0]

            index = deal_title_map[title]["index_list"][-1]
            if itype == "custom":
                ret_data = history_data[index][2]
            else:
                ret_data = history_data[index][3]

            monitor_len = ret_data.get("monitor_seconds", 10)

            if itype == "custom":
                duration, db_end_offset = self.get_custom_duration_by_title(title, ret_data)
            else:
                duration, db_end_offset = self.get_music_duration_by_title(title, ret_data)

            if db_end_offset > 0  and db_end_offset < duration:
                judge_size = abs(int(math.ceil(db_end_offset*1.0/monitor_len))) + 1
            if judge_size > 10:
                judge_size = 10
            if judge_size <= 3:
                judge_size = 3
                if itype == "custom":
                    judge_size = 1
        except Exception as e:
            self._dlog.logger.error("Error@delay_dynamic_judge_size", exc_info=True)
        return judge_size+1

    def fill_ret_data_by_acrid_count(self, sorted_title_list, history_data):
        try:
            ret_data = None
            init_ret_data = True
            for sitem in sorted_title_list:
                sitem_title, sitem_map = sitem
                sitem_title = self.tryStrSub(sitem_title)[0]
                sitem_count = sitem_map["count"]
                acrid_count_map = {}
                for tindex in sitem_map["index_list"]:
                    tdata = history_data[tindex][3]
                    if init_ret_data:
                        ret_data = copy.deepcopy(tdata)
                        ret_data["result"]["metadata"]["music"] = []
                        init_ret_data = False
                    if "metadata" in tdata["result"] and "music" in tdata["result"]["metadata"]:
                        for item in tdata['result']['metadata']['music']:
                            sim_title = self.tryStrSub(item['title'])[0]
                            if sim_title == sitem_title:
                                acrid = item['acrid']
                                if acrid not in acrid_count_map:
                                    acrid_count_map[acrid] = {"count":0, "info":item}
                                acrid_count_map[acrid]["count"] += 1
                if ret_data is None:
                    break

                acrid_count_map_sorted = sorted(acrid_count_map.items(), key=lambda x:x[1]["count"], reverse=True)
                for s_index, s_item in enumerate(acrid_count_map_sorted):
                    ret_data["result"]["metadata"]["music"].append(s_item[1]["info"])
                    if s_index >= 2:
                        break
            if ret_data is not None and len(ret_data['result']['metadata']['music']) > 6:
                ret_data['result']['metadata']['music'] = ret_data['result']['metadata']['music'][:6]
        except Exception as e:
            self._dlog.logger.error("Error@fill_ret_data_by_acrid_count", exc_info=True)
        return ret_data

    def get_music_data_offset(self, data):
        try:
            ret = {
                "monitor_len":0,
                "duration_ms":0,
                "s_begin_ms":0,
                "s_end_ms":0,
                "d_begin_ms":0,
                "d_end_ms":0
            }
            result = data.get("result")
            monitor_len = data.get("monitor_seconds", 10)
            ret["monitor_len"] = monitor_len
            if result and "metadata" in result and "music" in result["metadata"]:
                fitem = result["metadata"]["music"][0]
                ret["duration_ms"] = int(fitem["duration_ms"])
                ret["s_begin_ms"] = int(fitem["sample_begin_time_offset_ms"])
                ret["s_end_ms"] = int(fitem["sample_end_time_offset_ms"])
                ret["d_begin_ms"] = int(fitem["db_begin_time_offset_ms"])
                ret["d_end_ms"] = int(fitem["db_end_time_offset_ms"])
                return ret
        except Exception as e:
            self._dlog.logger.error("Error@get_music_data_offset, error_data:{0}".format(data), exc_info=True)
        return None

    def check_if_is_break(self, index1, index2, data1, data2):
        try:
            is_break = False
            ret1 = self.get_music_data_offset(data1)
            ret2 = self.get_music_data_offset(data2)
            if ret1 and ret2:
                diff_db = ret2["d_end_ms"] - ret1["d_begin_ms"]
                if diff_db <= 0:
                    return is_break
                timestamp1 = datetime.datetime.strptime(data1["timestamp"], "%H:%M:%S")
                timestamp2 = datetime.datetime.strptime(data2["timestamp"], "%H:%M:%S")
                monitor_len = ret1["monitor_len"]
                A1 = timestamp1 + relativedelta(seconds=int(ret1["s_begin_ms"]/1000))
                A2 = timestamp2 + relativedelta(seconds=int(ret2["s_end_ms"]/1000))
                B1 = int((A2 - A1).total_seconds())
                B2 = (index2 - index1 - 1)*monitor_len + int(diff_db/1000)
                B3 = int(diff_db/1000)
                if abs(B3 - B1) <= 15:
                    is_break = False
                elif abs(B2 - B1) <= 10:
                    is_break = True
        except Exception as e:
            self._dlog.logger.error("Error@check_if_is_break", exc_info=True)
        return is_break

    def check_if_continuous(self, index1, index2, data1, data2):
        try:
            is_cont = True
            ret1 = self.get_music_data_offset(data1)
            ret2 = self.get_music_data_offset(data2)
            timestamp1 = datetime.datetime.strptime(data1["timestamp"], "%H:%M:%S")
            timestamp2 = datetime.datetime.strptime(data2["timestamp"], "%H:%M:%S")
            diff_sec = (timestamp2 - timestamp1).total_seconds()
            monitor_len = ret1["monitor_len"]
            if ret1 and ret2:
                for tmp_ret in [ret1, ret2]:
                    if (tmp_ret["s_end_ms"] - tmp_ret["s_begin_ms"]) != (tmp_ret["d_end_ms"] - tmp_ret["d_begin_ms"]):
                        return is_cont
                dur1 = ret1["d_end_ms"] - ret1["d_begin_ms"]
                dur2 = ret2["d_end_ms"] - ret2["d_begin_ms"]
                dur1 = dur1 if dur1 > 0 else 0
                dur2 = dur2 if dur2 > 0 else 0
                ret1_s_end = ret1["s_end_ms"]
                ret2_s_begin = ret2["s_begin_ms"]
                if index1+1 == index2 and abs(monitor_len*1000 - ret1_s_end) < 2500 and abs(ret2_s_begin) < 2500 and diff_sec < monitor_len*2:
                    pass
                else:
                    ifirst, iend = max(ret1["d_begin_ms"], ret2["d_begin_ms"]), min(ret1["d_end_ms"], ret2["d_end_ms"])
                    inter_dur = iend - ifirst
                    if inter_dur > 0:
                        min_dur = min(dur1, dur2) if min(dur1, dur2) > 0 else max(dur1, dur2)
                        if min_dur > 0:
                            inter_rate = (inter_dur*1.0/min_dur)
                            if inter_dur >=2 and inter_rate >=0.8:
                                is_cont = False
        except Exception as e:
            self._dlog.logger.error("Error@check_if_continuous", exc_info=True)
        return is_cont

    def runDelayX_for_music_delay2(self, stream_id):
        history_data = self._delay_music[stream_id]
        judge_zero_or_latter = True

        if len(history_data) >= self._delay_list_threshold:
            history_data = history_data[-(self._delay_list_threshold-1):]

            history_data_len = len(history_data)
            for ii in range((history_data_len-1), 0, -1):
                if history_data[-ii][0][0] == NORESULT:
                    continue
                else:
                    history_data = history_data[-(ii+1):]
                    break

        first_not_noresult_index = -1
        for index, item in enumerate(history_data):
            if index == 0:
                continue
            if item[0] == NORESULT:
                first_not_noresult_index = index
            else:
                break
        if first_not_noresult_index != -1:
            history_data = history_data[first_not_noresult_index:]
            self._delay_music[stream_id] = history_data
            return None

        ########## Get Break Index ##########
        deal_title_map = {} #key:title, value:{'count':0, 'index_list':[]}
        break_index = 0


        for index, item in enumerate(history_data[1:]):
            index += 1
            raw_title, sim_title, timestamp, data = item
            if index!=1:
                flag_first = True
                flag_second = True
                if sim_title in deal_title_map:
                    flag_first = False
                if flag_first:
                    tmp_all_len = len(history_data)
                    tmp_count = 0
                    tmp_first_break_index = -1
                    #tmp_judge_size = 2
                    tmp_judge_size = self.delay_dynamic_judge_size(deal_title_map, history_data, "music")
                    find_interval = False
                    find_pre_last_index = index-1
                    find_next_sim_index = -1
                    for i in range(index, tmp_all_len):
                        next_raw_title, next_sim_title, next_timestamp, next_data = history_data[i]
                        tmp_list_flag = False
                        if next_sim_title in deal_title_map:
                            tmp_list_flag = True
                            tmp_count = 0
                            tmp_first_break_index = -1
                            if find_interval == True:
                                find_interval = False
                                find_next_sim_index = i
                                if find_next_sim_index - find_pre_last_index - 1 >= 8:
                                    is_break = self.check_if_is_break(find_pre_last_index, find_next_sim_index, history_data[find_pre_last_index][3], history_data[find_next_sim_index][3])
                                    if is_break:
                                        break_index = find_pre_last_index + 1
                                        break
                        else:
                            if find_interval == False:
                                find_interval = True
                                find_pre_last_index = i - 1

                        if tmp_list_flag:
                            continue
                        else:
                            tmp_count += 1
                            if tmp_first_break_index == -1:
                                tmp_first_break_index = i
                            if tmp_count < tmp_judge_size:
                                continue
                            flag_second = True
                            break_index = tmp_first_break_index if tmp_first_break_index != -1 else i
                            break

                if flag_first and flag_second and deal_title_map:
                    if break_index >0:
                        for iii in range(index, break_index):
                            tmp_raw_title, tmp_sim_title, tmp_timestamp, tmp_data = history_data[iii]
                            if tmp_sim_title == NORESULT:
                                continue
                            if tmp_sim_title in deal_title_map:
                                deal_title_map[tmp_sim_title]['count'] += 1
                                deal_title_map[tmp_sim_title]['index_list'].append(iii)
                        #**********************************************************
                        sorted_dtitle = sorted(deal_title_map.items(), key = lambda x:x[1]['count'], reverse = True)
                        sorted_fitem_title, sorted_fitem_map = sorted_dtitle[0]
                        sfm_count = sorted_fitem_map["count"]
                        cfirst_index, csecond_index = sorted(sorted_fitem_map["index_list"])[:2] if sfm_count >=2 else [0, 0]
                        if sfm_count in [2, 3]: #or ((3 < sfm_count <= 10) and sfm_count < (break_index - index)):
                            is_cont = self.check_if_continuous(cfirst_index, csecond_index, history_data[cfirst_index][3], history_data[csecond_index][3])
                            if not is_cont:
                                judge_zero_or_latter = False
                                break_index = cfirst_index + 1
                                deal_title_map = {sorted_fitem_title:{'count':1, 'index_list':[cfirst_index]}}
                        #**********************************************************
                    #跳出
                    break

            if sim_title == NORESULT:
                continue
            if sim_title not in deal_title_map:
                deal_title_map[sim_title] ={'count':0, 'index_list':[]}
            deal_title_map[sim_title]['count'] += 1
            deal_title_map[sim_title]['index_list'].append(index)


        ret_data = None
        duration_dict = {}
        duration = 0
        if break_index > 0 and deal_title_map:
            sorted_title_list = sorted(deal_title_map.items(), key = lambda x:x[1]['count'], reverse = True)
            ret_data = self.fill_ret_data_by_acrid_count(sorted_title_list, history_data)
            if ret_data and len(ret_data["result"]["metadata"]["music"]) == 0:
                ret_data = None

            index_range = set()
            for title in deal_title_map:
                index_range |= set(deal_title_map[title]['index_list'])
            min_index = min(index_range)
            max_index = max(index_range)
            duration_dict = self.compute_played_duration(history_data, min_index, max_index, judge_zero_or_latter, "music")

            self.remove_next_result_from_now_result_list_for_music_delay2(history_data, ret_data, max_index)

        if ret_data:
            duration = duration_dict["duration"]
            duration_accurate = duration_dict["duration_accurate"]
            sample_duration = duration_dict["sample_duration"]
            db_duration = duration_dict["db_duration"]
            mix_duration = duration_dict["mix_duration"]
            accurate_timestamp_utc = duration_dict["accurate_timestamp_utc"]
            ret_data['result']['metadata']['played_duration'] = abs(mix_duration)
            ret_data['result']['metadata']['timestamp_utc'] = accurate_timestamp_utc
            ret_data['timestamp'] = accurate_timestamp_utc
            if ret_data['result']['metadata']['played_duration'] <= 1:
                ret_data = None

        ########### cut history_data #############
        if break_index>=0:
            cut_index = break_index
            for i, item in enumerate(history_data[break_index:]):
                if item[0][0] == NORESULT:
                    cut_index = break_index + i + 1
                else:
                    break
            cut_index = cut_index - 1 if cut_index >= 1 else cut_index
            history_data = history_data[cut_index:]

            reverse_index = -1
            for i, item in enumerate(history_data[::-1]):
                if item[0][0] == NORESULT:
                    reverse_index = i
                    continue
                else:
                    break

            if reverse_index != -1:
                new_cut_index = -1
                reverse_index = len(history_data) - reverse_index - 1
                if reverse_index in [0, 1]:
                    history_data = []
                else:
                    pass

            if judge_zero_or_latter == False and len(history_data) > 0:
                if history_data[0][0] != NORESULT:
                    tmp_t, sim_tmp_t, tmp_timestamp, tmp_data = history_data[0]
                    if tmp_data and "status" in tmp_data["result"]:
                        tmp_data["result"]["status"]["code"] = 1001
                        history_data[0] = (NORESULT, NORESULT, tmp_timestamp, tmp_data)
            self._delay_music[stream_id] = history_data

        return ret_data


    def deal_real_custom(self, data):
        is_new = False
        result = None
        curr_title = self.get_mutil_result_acrid(data, 'custom')[0]

        stream_id = data.get("stream_id")
        timestamp = data.get("timestamp")
        timestamp_obj = datetime.datetime.strptime(timestamp, "%H:%M:%S")
        if not stream_id:
            return result, is_new
        if curr_title == NORESULT:
            if not self.real_check_title_custom(stream_id, curr_title, timestamp_obj):
                self._real_custom[stream_id][0].append((curr_title, timestamp))
                self._real_custom[stream_id][1] = data
                result = data
                is_new = True
            else:
                result = None
                is_new = False
        else:
            if self.real_check_title_custom(stream_id, curr_title, timestamp_obj):
                result = self._real_custom[stream_id][1]
                is_new = False
            else:
                self._real_custom[stream_id][0].append((curr_title, timestamp))
                self._real_custom[stream_id][1] = data
                result = data
                is_new = True
        return result, is_new

    def deal_delay_custom(self, data):
        try:
            ret_result = None
            stream_id = data.get("stream_id")
            timestamp = data.get("timestamp")
            title_list = self.get_mutil_result_acrid(data, 'custom', 5)
            if stream_id not in self._delay_custom:
                self._delay_custom[stream_id] = [(title_list, timestamp, data)]
            else:
                self._delay_custom[stream_id].append((title_list, timestamp, data))

            if len(self._delay_custom[stream_id]) >= self._delay_list_max_num:
                ret_result = self.runDelayX_custom(stream_id)
        except Exception as e:
            self._dlog.logger.error("Error@deal_delay_custom", exc_info=True)
        return ret_result

    def remove_next_result_from_now_result_list(self, history_data, ret_data, max_index):
        #Just for custom delay filter
        try:
            if ret_data and len(history_data) >= max_index+2:
                acrid_list, timestamp, next_data = history_data[max_index + 1]
                if next_data:
                    #update max size acrid_list to 20
                    next_acrid_list = self.get_mutil_result_acrid(next_data, 'custom', 20)
                    next_acrid_set = set(next_acrid_list)
                    new_ret_custom_files = []
                    for index, item in enumerate(ret_data["result"]["metadata"]["custom_files"]):
                        if index == 0 or (item["acrid"] not in next_acrid_set):
                            new_ret_custom_files.append(item)
                    ret_data["result"]["metadata"]["custom_files"] = new_ret_custom_files
        except Exception as e:
            self._dlog.logger.error("Error@remove_next_result_from_now_result_list", exc_info=True)

    def get_custom_duration_by_title(self, title, ret_data):
        try:
            duration = 0
            for index, item in enumerate(ret_data["result"]["metadata"]["custom_files"]):
                if title == item["acrid"]:
                    duration_ms = int(item["duration_ms"])
                    if duration_ms >= 0:
                        duration = int(duration_ms/1000)
        except Exception as e:
            self._dlog.logger.error("Error@get_custom_duration_by_title, error_data:{0}".format(ret_data), exc_info=True)
        return duration

    def custom_delay_dynamic_judge_size(self, deal_title_map, history_data):
        try:
            judge_size = 6
            title = list(deal_title_map.keys())[0]
            index = deal_title_map[title]["index_list"][-1]
            ret_data = history_data[index][2]
            duration = self.get_custom_duration_by_title(title, ret_data)
            tmp_size = int(duration/10)
            if tmp_size <=6:
                judge_size = tmp_size if tmp_size > 1 else 2
            elif tmp_size >= 18:
                judge_size = 18
        except Exception as e:
            self._dlog.logger.error("Error@custom_delay_dynamic_judge_size", exc_info=True)

        return judge_size if judge_size >= 2 else 2

    def runDelayX_custom(self, stream_id):
        history_data = self._delay_custom[stream_id]

        if len(history_data) >= self._delay_list_threshold:
            history_data = history_data[-(self._delay_list_threshold-1):]

            history_data_len = len(history_data)
            for ii in range((history_data_len-1), 0, -1):
                if history_data[-ii][0][0] == NORESULT:
                    continue
                else:
                    history_data = history_data[-(ii+1):]
                    break

        first_not_noresult_index = -1
        for index, item in enumerate(history_data):
            if index == 0:
                continue
            if len(item[0])>0 and item[0][0] == NORESULT:
                first_not_noresult_index = index
            else:
                break
        if first_not_noresult_index != -1:
            history_data = history_data[first_not_noresult_index:]
            self._delay_custom[stream_id] = history_data
            return None

        deal_title_map = {} #key:title, value:{'count':0, 'index_list':[]}
        tmp_deal_title_map = {}
        break_index = 0

        for index, item in enumerate(history_data[1:]):
            index += 1
            title_list, timestamp, data = item
            if index!=1:
                flag_first = True
                flag_second = True
                for title in title_list[:3]:
                    if title in deal_title_map:
                        flag_first = False
                if flag_first:
                    judge_size = self.custom_delay_dynamic_judge_size(deal_title_map, history_data)
                    for i in range(1,judge_size):
                        if index + i < len(history_data):
                            next_title_list, next_timestamp, next_data = history_data[index + i]
                            for title in next_title_list[:3]:
                                if title in deal_title_map:
                                    flag_second = False
                        else:
                            flag_second = False
                if flag_first and flag_second and deal_title_map:
                    break_index = index
                    break

            for i, title in enumerate(title_list):
                if title == NORESULT:
                    continue
                if i == 0:
                    if title not in deal_title_map:
                        deal_title_map[title] ={'count':0, 'index_list':[]}
                    deal_title_map[title]['count'] += 1
                    deal_title_map[title]['index_list'].append(index)
                if title not in tmp_deal_title_map:
                    tmp_deal_title_map[title] = {'count':0, 'index_list':[]}
                tmp_deal_title_map[title]['count'] += 1
                tmp_deal_title_map[title]['index_list'].append(index)

        ########### New Deal Custom Result Add Count ###########
        ret_data = None
        duration_dict = {}
        duration = 0
        if break_index > 0 and deal_title_map:
            tmp_count_map = {}
            sorted_title_list = sorted(deal_title_map.items(), key = lambda x:x[1]['count'], reverse = True)
            for sitem in sorted_title_list:
                sitem_title, sitem_map = sitem
                sitem_count = sitem_map["count"]
                sitem_min_index = min(sitem_map["index_list"])
                if sitem_count not in tmp_count_map:
                    tmp_count_map[sitem_count] = []
                tmp_count_map[sitem_count].append((sitem_title, sitem_min_index))
            first_item_flag = True
            for scount in sorted(tmp_count_map.keys(), reverse=True):
                count_list = sorted(tmp_count_map[scount], key = lambda x:x[1])
                for ditem in count_list:
                    dtitle, dindex = ditem
                    from_data = history_data[dindex][2]
                    if first_item_flag:
                        first_item_flag = False
                        ret_data = copy.deepcopy(from_data)
                        ret_data["result"]["metadata"]["custom_files"] = []
                    self.custom_result_append(ret_data, dtitle, from_data, scount, tmp_deal_title_map)

            index_range = set()
            for title in deal_title_map:
                index_range |= set(deal_title_map[title]['index_list'])
            min_index = min(index_range)
            max_index = max(index_range)
            duration_dict = self.compute_played_duration(history_data, min_index, max_index, True, "custom")

            self.remove_next_result_from_now_result_list(history_data, ret_data, max_index)

        if ret_data:
            duration = duration_dict["duration"]
            duration_accurate = duration_dict["duration_accurate"]
            sample_duration = duration_dict["sample_duration"]
            db_duration = duration_dict["db_duration"]
            mix_duration = duration_dict["mix_duration"]
            accurate_timestamp_utc = duration_dict["accurate_timestamp_utc"]
            ret_data['result']['metadata']['played_duration'] = abs(mix_duration)
            ret_data['result']['metadata']['timestamp_utc'] = accurate_timestamp_utc
            ret_data['timestamp'] = accurate_timestamp_utc
            if ret_data['result']['metadata']['played_duration'] <= self._delay_custom_played_duration_min:
                ret_data = None

        ########### cut history_data #############
        if break_index>=0:
            cut_index = break_index
            for i, item in enumerate(history_data[break_index:]):
                if item[0][0] == NORESULT:
                    cut_index = break_index + i + 1
                else:
                    break
            cut_index = cut_index - 1 if cut_index >= 1 else cut_index
            history_data = history_data[cut_index:]

            reverse_index = -1
            for i, item in enumerate(history_data[::-1]):
                if item[0][0] == NORESULT:
                    reverse_index = i
                    continue
                else:
                    break

            if reverse_index != -1:
                new_cut_index = -1
                reverse_index = len(history_data) - reverse_index - 1
                if reverse_index in [0, 1]:
                    history_data = []
                else:
                    pass

            self._delay_custom[stream_id] = history_data
        return ret_data

class FilterWorker:
    def __init__(self):
        self.tmp_no_result = {'status': {'msg': 'No result', 'code': 1001, 'version': '1.0'}, 'metadata': {}}
        self._result_map = []
        self.init_logger()
        self._result_filter = ResultFilter(self.dlog)

    def init_logger(self):
        self.dlog = acrcloud_logger.AcrcloudLogger('Filter_Log')
        self.dlog.addStreamHandler()

    def save_one_delay(self, old_data, isCustom=0):
        data = None
        if isCustom:
            data = self._result_filter.deal_delay_custom(old_data)
        else:
            data = self._result_filter.deal_delay_history(old_data)

        if data is not None:
            del data["stream_id"]
            self._result_map.append(data)
            return True
        else:
            return False

    def save_one(self, jsondata):
        try:
            timestamp = jsondata['timestamp']
            if jsondata['result']['status']['code'] != 0:
                jsondata['result']['metadata'] = {'timestamp_utc':timestamp}
            elif 'metadata' in jsondata['result']:
                jsondata['result']['metadata']['timestamp_utc'] = timestamp

            tmp_no_result_json = {'status': {'msg': 'No result', 'code': 1001, 'version': '1.0'}, 'metadata': {'timestamp_utc': timestamp}}

            ret = False
            custom_data = copy.deepcopy(jsondata)
            if jsondata['result']['status']['code'] != 0:
                ret = self.save_one_delay(jsondata, 0)
                ret = self.save_one_delay(custom_data, 1)
            elif 'metadata' in jsondata['result'] and 'custom_files' in jsondata['result']['metadata']:
                if 'music' in jsondata['result']['metadata']:
                    del custom_data['result']['metadata']['music']
                    del jsondata['result']['metadata']['custom_files']
                    ret = self.save_one_delay(jsondata, 0)
                else:
                    jsondata['result'] = copy.deepcopy(tmp_no_result_json)
                    ret = self.save_one_delay(jsondata, 0)
                ret = self.save_one_delay(custom_data, 1)
            elif 'metadata' in jsondata['result'] and 'music' in jsondata['result']['metadata']:
                custom_data['result'] = copy.deepcopy(tmp_no_result_json)
                ret = self.save_one_delay(jsondata, 0)
        except Exception as e:
            self.dlog.logger.error("Error@save_one", exc_info=True)
        return ret

    def do_filter(self, tmp_id, filepath, result, rec_length, timestamp):
        try:
            jsoninfo = {
                "stream_id": tmp_id,
                "file":filepath,
                "rec_length": rec_length,
                "result": result,
                "timestamp": timestamp
            }
            self.save_one(jsoninfo)
        except Exception as e:
            self.dlog.logger.error("Error@do_filter", exc_info=True)

    def end_filter(self, tmp_id, rec_length, timestamp):
        try:
            tmp_no_result = copy.deepcopy(self.tmp_no_result)
            for i in range(1, 60):
                tmp_timestamp = datetime.datetime.strptime(timestamp, "%H:%M:%S")
                new_timestamp = (tmp_timestamp + relativedelta(seconds=int(i*rec_length))).strftime("%H:%M:%S")
                jsoninfo = {
                    "stream_id": tmp_id,
                    "rec_length": rec_length,
                    "result": tmp_no_result,
                    "timestamp": new_timestamp
                }
                self.save_one(jsoninfo)
        except Exception as e:
            self.dlog.logger.error("Error@end_filter", exc_info=True)

    def start_filter(self, tmp_id, rec_length, timestamp):
        try:
            tmp_no_result = copy.deepcopy(self.tmp_no_result)
            for i in range(1, 0, -1):
                new_timestamp = timestamp
                jsoninfo = {
                    "stream_id": tmp_id,
                    "rec_length": rec_length,
                    "result": tmp_no_result,
                    "timestamp": new_timestamp
                }
                self.save_one(jsoninfo)
        except Exception as e:
            self.dlog.logger.error("Error@start_filter", exc_info=True)

    def apply_filter(self, result_list):
        try:
            appid = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
            rec_length = 10
            timestamp = None
            for index, item in enumerate(result_list):
                filename = item["file"]
                timestamp = item["timestamp"]
                rec_length = item["rec_length"]
                if index == 0:
                    self.start_filter(appid, rec_length, timestamp)
                result = item["result"]
                if "status" in result and result["status"]["code"] in [0, 1001]:
                    self.do_filter(appid, filename, result, rec_length, timestamp)
            if timestamp is not None:
                self.end_filter(appid, rec_length, timestamp)
        except Exception as e:
            self.dlog.logger.error("Error@apply_filter", exc_info=True)
        return self._result_map

    def test(self):
        a = '{"timestamp": "01 00:17:40", "rec_length": 10, "result": {"status": {"msg": "Success", "code": 0, "version": "1.0"}, "cost_time": 1.2630000114441, "result_type": 0, "metadata": {"timestamp_utc": "2018-08-02 14:44:39", "music": [{"album": {"name": "Solino"}, "play_offset_ms": 85200, "sample_begin_time_offset_ms": 300, "title": "La Bambola", "result_from": 1, "release_date": "2002-10-28", "sample_end_time_offset_ms": 9460, "genres": [{"name": "Pop"}], "label": "Amiga", "db_end_time_offset_ms": 85120, "score": 82, "db_begin_time_offset_ms": 75960, "artists": [{"name": "Patty Pravo"}], "duration_ms": 182200, "external_ids": {"isrc": "ITB006870616", "upc": "743219711328"}, "acrid": "27fef80da4dabc33591a2c08a08edaf0", "external_metadata": {"spotify": {"album": {"name": "Solino", "id": "0I3MXd5FYGAj6X9GOJepMb"}, "track": {"name": "La Bambola", "id": "5YT3WdXo5gBwZ0TlJiB0TE"}, "artists": [{"name": "Patty Pravo", "id": "2Yi5fknmHBqqKjHF6cXQyh"}]}, "deezer": {"album": {"name": "Solino", "id": "112016"}, "track": {"name": "La Bambola", "id": "1017795"}, "artists": [{"name": "Patty Pravo", "id": "58615"}]}, "youtube": {"vid": "UHCgZY-HX6U"}}}]}}, "file": "radioairplay_19/501.2018.06.19.04.00.00.mp3"}'
        data = json.loads(a)
        raw_title = self._result_filter.get_mutil_result_title(data, 'music', 1)[0]
        sim_title = self._result_filter.tryStrSub(raw_title)
        print(raw_title, sim_title)
