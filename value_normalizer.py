import re


def isstring(value): return isinstance(value, str)


def isfloat(value: str): return (re.match(r'^-?\d+(?:\.\d+)?$', value) is not None)


def isinteger(value: str): return (re.match('^\d+$', value) is not None)


def isvalidmetric(value) : return isinstance(value, int) or isinstance(value, float) or isinstance(value, bool)

def normalize_data(data):
    if isinstance(data, dict):
        for key in data:

            value = data.get(key)

            if isstring(value):
                value = remove_data_unit(value)
                if isinteger(value):
                    data[key] = int(value)
                    continue
                if isfloat(value):
                    data[key] = float(value)
                    continue


    return data


def remove_data_unit(value: str):
    return value.replace(" kB", "")
