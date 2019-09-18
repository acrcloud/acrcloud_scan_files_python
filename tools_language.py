#!/usr/bin/env python
#-*- coding:utf-8 -*-

class tools_language:
    def __init__(self):
        pass

    def is_chinese(self, uchar):
        if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
            return True
        else:
            return False

    def is_CJK(self, uchar):
        """判断一个unicode是否为CJK(中日韩)"""
        if uchar >= u'\u3000' and uchar <= u'\u303f':
            return True
        elif uchar >= u'\u3040' and uchar <= u'\u309f':
            return True
        elif uchar >= u'\u30a0' and uchar <= u'\u30ff':
            return True
        elif uchar >= u'\uff00' and uchar <= u'\u30ff':
            return True
        elif uchar >= u'\u4e00' and uchar <= u'\u9faf':
            return True
        elif uchar >= u'\u3400' and uchar <= u'\u4dbf':
            return True
        elif uchar >= u'\u0400' and uchar <= u'\u052f': #俄语
            return True
        elif uchar >= u'\uac00' and uchar <= u'\ud7ff': #韩文
            return True
        elif uchar >= u'\u4e00' and uchar <= u'\u9fa5': #中文
            return True
        elif uchar >= u'\uff61' and uchar <= u'\uff9f': #半角日文 半宽假名
            return True
        else:
            return False

    def is_number(self, uchar):
        if uchar >= u'\u0030' and uchar<=u'\uffef':
            return True
        else:
            return False

    def is_alphabet(self, uchar):
        if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
            return True
        else:
            return False

    def is_other(self, uchar):
        if not (self.is_chinese(uchar) or self.is_number(uchar) or self.is_alphabet(uchar)):
            return True
        else:
            return False

    def B2Q(self, uchar):
        inside_code=ord(uchar)
        if inside_code<0x0020 or inside_code>0x7e:
            return uchar
        if inside_code==0x0020:
            inside_code=0x3000
        else:
            inside_code+=0xfee0
        return unichr(inside_code)

    def Q2B(self, uchar):
        inside_code=ord(uchar)
        if inside_code==0x3000:
            inside_code=0x0020
        else:
            inside_code-=0xfee0
        if inside_code<0x0020 or inside_code>0x7e:
            return uchar
        return unichr(inside_code)

    def stringQ2B(self, ustring):
        return "".join([self.Q2B(uchar) for uchar in ustring])

    def uniform(self, ustring):
        return self.stringQ2B(ustring).lower()

    def string2List(self, ustring):
        retList=[]
        utmp=[]
        for uchar in ustring:
            if self.is_other(uchar):
                if len(utmp)==0:
                    continue
                else:
                    retList.append("".join(utmp))
                    utmp=[]
            else:
                utmp.append(uchar)
        if len(utmp)!=0:
            retList.append("".join(utmp))
        return retList

    def has_chinese(self, ustring):
        ustring_lower = ustring.lower()
        for uchar in ustring_lower:
            if self.is_chinese(uchar):
                return True
        return False

    def has_CJK(self, ustring):
        ustring_lower = ustring.lower()
        for uchar in ustring_lower:
            if self.is_CJK(uchar):
                return True
        return False


