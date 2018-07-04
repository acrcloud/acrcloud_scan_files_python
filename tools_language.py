#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
author: quqiang
date: 2015/07/31

ps: code from web
汉字处理的工具:
判断unicode是否是汉字，数字，英文，或者其他字符
全角符号转半角符号


#编码范围链接:http://www.rikai.com/library/kanjitables/kanji_codes.unicode.shtml
Unicode Kanji Table(Unicode 汉子表)
    1. Japanese-style punctuation (3000 - 303f) #日式标点符号（3000 - 303f）
    2. Hiragana (3040 - 309f) #平假名（3040 - 309f）
    3. Katakana (30a0 - 30ff) #片假名（30a0 - 30ff）
    4. Full-width roman characters and half-width katakana (ff00 - ffef) #全角罗马字符和半角片假名（ff00 - ffef）
    5. CJK unifed ideographs - Common and uncommon kanji (4e00 - 9faf) #CJK - 常见和罕见的汉字（4e00 - 9faf）
    6. CJK unified ideographs Extension A - Rare kanji (3400 - 4dbf) #CJK统一表意文字扩展名A-罕见的汉字（3400 - 4dbf）

俄语的范围:
    x0400-x052f  # Cyrillic: 0400-04ff, Cyrillic Supplementary:0500-052F

范围列表：https://gist.github.com/shingchi/64c04e0dd2cbbfbc1350
"""

class tools_language:
    def __init__(self):
        pass

    def is_chinese(self, uchar):
        """判断一个unicode是否是汉字"""
        if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
            return True
        else:
            return False

    def is_japanese(self, uchar):
        """判断一个unicode是否是日语"""
        if uchar >= u'\u3040' and uchar<=u'\u309f':
            return True
        elif uchar >= u'\u30a0' and uchar<=u'\u30ff':
            return True
        elif uchar >= u'\u31F0' and uchar<=u'\u31FF':
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
        elif uchar >= u'\u0400' and uchar <= u'\u052f':
            return True
        else:
            return False

    def is_number(self, uchar):
        """判断一个unicode是否是数字"""
        if uchar >= u'\u0030' and uchar<=u'\uffef':
            return True
        else:
            return False

    def is_alphabet(self, uchar):
        """判断一个unicode是否是英文字母"""
        if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
            return True
        else:
            return False

    def is_other(self, uchar):
        """判断是否非汉字，数字和英文字符"""
        if not (self.is_chinese(uchar) or self.is_number(uchar) or self.is_alphabet(uchar)):
            return True
        else:
            return False

    def B2Q(self, uchar):
        """半角转全角"""
        inside_code=ord(uchar)
        #不是半角字符就返回原来的字符
        if inside_code<0x0020 or inside_code>0x7e:
            return uchar
        #除了空格其他的全角半角的公式为:半角=全角-0xfee0
        if inside_code==0x0020:
            inside_code=0x3000
        else:
            inside_code+=0xfee0
        return unichr(inside_code)

    def Q2B(self, uchar):
        """全角转半角"""
        inside_code=ord(uchar)
        if inside_code==0x3000:
            inside_code=0x0020
        else:
            inside_code-=0xfee0
        #转完之后不是半角字符返回原来的字符
        if inside_code<0x0020 or inside_code>0x7e:
            return uchar
        return unichr(inside_code)

    def stringQ2B(self, ustring):
        """把字符串全角转半角"""
        return "".join([self.Q2B(uchar) for uchar in ustring])

    def uniform(self, ustring):
        """格式化字符串，完成全角转半角，大写转小写的工作"""
        return self.stringQ2B(ustring).lower()

    def string2List(self, ustring):
        """将ustring按照中文，字母，数字分开"""
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

    def has_japanese(self, ustring):
        ustring_lower = ustring.lower()
        for uchar in ustring_lower:
            if self.is_japanese(uchar):
                return True
        return False



if __name__ == "__main__":
    hello = tools_language()
    ustring = [u'中文lk', 'so what', u'コードペンディンス', u'ネグリータ', u'日本語']
    for item in ustring:
        print item, hello.has_CJK(item), hello.has_japanese(item)
