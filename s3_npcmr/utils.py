import os
import datetime


def get_name_from_path(path):
    name = os.path.splitext(os.path.basename(path))[0]
    return name


def get_extension_from_path(path):
    extension = os.path.splitext(os.path.basename(path))[1][1:]
    return extension


def get_default_for_json_dump(o):
    """
    for transforming datetime in json.dumps(my_json, default=get_default_for_json_dump)

    Otherwise:
    TypeError: Object of type 'datetime' is not JSON serializable
    """
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
