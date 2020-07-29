import re


def isstring(value): return isinstance(value, str)
def isfloat(value: str): return (re.match(r'^-?\d+(?:\.\d+)?$', value) is not None)
def isinteger(value: str): return (re.match('^\d+$', value) is not None)
def isvalidmetric(value) : return isinstance(value, int) or isinstance(value, float) or isinstance(value, bool)

type_mapping = {
    "yes" : 1,
    "no" : 0,
    "up" : 1,
    "down" : 0,
    True: 1,
    False: 0,
    "MOUNTED" : 1,
    "UNMOUNTED" : 0
}

def normalize_value(value):

    if value is None:
        return None

    value = type_mapping.get(value) if type_mapping.get(value) is not None else value

    if isstring(value):
        value = parse_string(value)

    if isvalidmetric(value):
        return value
    else:
        print("WARN Value: " + str(value) + " is not valid metric type")
        return None


def parse_string(value):

    value = remove_data_unit(value)

    if isinteger(value):
        value = int(value)
    elif isfloat(value):
        value = float(value)

    return value


def remove_data_unit(value: str):
    return value.replace(" kB", "")
