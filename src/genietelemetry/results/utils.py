import pickle
from datetime import datetime, timedelta, timezone

def massage_meta(input_):

    # no input or empty input
    if not input_:
        return {}

    try:
        pickle.dumps(input_)
    except PicklingError as e:
        raise AttributeError('Status Meta [%s] contains unpicklable value'
                             % input_, e)

    # populate key, datetime in isoformat with utz timezone
    key = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    # if not dictionary
    if not isinstance(input_, dict):
        return { key: input_ }

    # loop over dictionary and validate all keys
    for k in input_.keys():
        try:
            str_to_datetime(k)
        except Exception:
            break
    else:
        # all keys are datetime string
        return input_
    # wrap with datetime key
    return { key: input_ }

def str_to_datetime(input_):
    # convert from datetime str to datetime instance
    dt, _, us = input_.partition(".")
    dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    dt.replace(tzinfo=timezone.utc)
    us = int(us.rstrip("Z"), 10)
    return dt + timedelta(microseconds = us)