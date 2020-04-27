
# -*- coding: utf-8 -*-

def format_temp(int1, int2):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    int2 = int(int2)
    result = int1 + (int2 << 8)
    # Divide by 100 to get actual float
    # PY2 note: make sure you import division from __future__
    result = result / 100
    # Now to handle negative numbers
    if result > 128:
        result = result - 256
    # Only want max 2 decimal precision
    result = round(result, 2)
    return result


def format_humidity(int1, int2):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    int2 = int(int2)
    result = int1 + (int2 << 8)
    # Divide by 100 to get actual percentage
    # PY2 note: make sure you import division from __future__
    result = result / 100
    # Only want max 2 decimal precision
    result = round(result, 2)
    return result


def format_doorstatus(int1):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    if int1 == 0:
        result = "CLOSED"
    else:
        result = "OPEN"
    return result


def format_waterstatus(int1):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    if int1 == 0:
        result = "DRY"
    else:
        result = "WET"
    return result


def format_lowbat(int1):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    if int1 == 0:
        result = False
    else:
        result = True
    return result
