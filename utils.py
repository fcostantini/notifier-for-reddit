import re


def convert65536(s):
    l = list(s)
    i = 0
    while i < len(l):
        o = ord(l[i])
        if o > 65535:
            l[i] = "{"+str(o)+"ū}"
        i += 1
    return "".join(l)


def parse65536(match):
    mtext = int(match.group()[1:-2])
    if mtext > 65535:
        return chr(mtext)
    else:
        return "ᗍ" + str(mtext) + "ūᗍ"


def convert65536back(s):
    while re.search(r"{\d\d\d\d\d+ū}", s) is not None:
        s = re.sub(r"{\d\d\d\d\d+ū}", parse65536, s)
    s = re.sub(r"ᗍ(\d\d\d\d\d+)ūᗍ", r"{\1ū}", s)
    return s