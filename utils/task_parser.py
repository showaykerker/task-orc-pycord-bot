import datetime
import json
import numpy as np

from collections import defaultdict
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

weekday_definition = {
    "一": 0, "二": 1, "三": 2, "四": 3,"五": 4, "六": 5, "日": 6,
    "mo.": 0, "tu.": 1, "we.": 2, "th.": 3,"fr.": 4, "sa.": 5, "su.": 6
}

def weekday_to_date(weekday, date_overwrite=None):
    assert isinstance(weekday, int) and 0 <= weekday <= 6
    curr = date_overwrite or datetime.datetime.now().date()
    curr_wd = curr.weekday()
    weekday -= curr_wd
    weekdaydelta = weekday if weekday >= 0 else weekday + 7
    return curr + relativedelta(days= weekdaydelta)

def validate(date_text, date_overwrite=None, check_over=True):

    date = None
    all_digits = False
    date_text = str(date_text)
    try:
        if all([isinstance(int(d), int) for d in date_text]):
            all_digits = True
    except ValueError:
        pass

    if all_digits:
        date_text = str(date_text)
        if len(date_text) == 3:  # handle format 0MDD
            date_text = f"0{date_text[:1]}/{date_text[1:]}"
        elif len(date_text) == 4:  # handle format MMDD
            date_text = f"{date_text[:2]}/{date_text[2:]}"
        elif len(date_text) == 6:  # handle format YYMMDD
            date_text = f"20{date_text[:2]}/{date_text[2:4]}/{date_text[4:]}"
        elif len(date_text) == 8:  # handle format YYYYMMDD
            date_text = f"{date_text[:4]}/{date_text[4:6]}/{date_text[6:]}"

    try:
        date = parse(date_text)
    except ValueError:
        pass

    if date is None:
        return None

    date = date.date()

    target_datetime = date_overwrite or datetime.datetime.now().date()

    if date < target_datetime and check_over:
        date += relativedelta(years=1)

    return date

def parse_tasks(msgs):
    structured = {"task_assignment": {np.inf: defaultdict(list, {})}, "schedule": defaultdict(list, {})}
    current_asignee = None
    current_schedule = None
    interested_dict = structured["task_assignment"][np.inf]
    last_line = None
    date_overwrite = None
    msgs = msgs if isinstance(msgs, list) else msgs.split("\n")
    for msg in msgs:
        if msg.startswith("SetDate"):
            date_overwrite = validate(msg.split(" ")[1], check_over=False)
            continue
        elif msg.startswith("@"):  # handle name
            current_asignee = msg[1:]
            current_schedule = None
            structured["task_assignment"][current_asignee.strip()] = defaultdict(list, {np.inf: []})
            interested_dict = structured["task_assignment"][current_asignee.strip()]
        elif msg.endswith("時程") and last_line == "":
            current_schedule = msg
            current_asignee = None
            structured["schedule"][msg.strip()] = defaultdict(list, {np.inf: []})
            interested_dict = structured["schedule"][msg.strip()]
        elif msg.lower().startswith(tuple(weekday_definition.keys())):
            wd = weekday_definition[msg.lower().split(" ")[0]]
            d = weekday_to_date(wd, date_overwrite=date_overwrite)
            interested_dict[d.strftime(format="%Y/%m/%d")].append(" ".join(msg.split(" ")[1:]))
        elif msg.count(" ") == 0 and len(msg):  # handle date-alike tasks
            interested_dict[np.inf].append(msg)
        elif d:= validate(msg.split(" ")[0], date_overwrite=date_overwrite):  # handle date
            interested_dict[d.strftime(format="%Y/%m/%d")].append(" ".join(msg.split(" ")[1:]))
        elif msg in ["", "\n", None]:  # handle spaces
            pass
        else:
            interested_dict[np.inf].append(msg)
        last_line = msg
    print(json.dumps(structured, indent=4, ensure_ascii=False))
    return structured