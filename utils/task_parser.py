import json
import datetime
import numpy as np
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from collections import defaultdict

weekday_definition = {
    "一": 0, "二": 1, "三": 2, "四": 3,"五": 4, "六": 5, "日": 6,
    "mo.": 0, "tu.": 1, "we.": 2, "th.": 3,"fr.": 4, "sa.": 5, "su.": 6
}

def weekday_to_date(weekday):
    assert isinstance(weekday, int) and 0 <= weekday <= 6
    curr = datetime.datetime.now().date()
    curr_wd = curr.weekday()
    weekday -= curr_wd
    weekdaydelta = weekday if weekday >= 0 else weekday + 7
    return curr + relativedelta(days= weekdaydelta)

def validate(date_text):

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
            date_text = f"{date_text[:2]}/{date_text[2:4]}/{date_text[4:]}"
        elif len(date_text) == 8:  # handle format YYYYMMDD
            date_text = f"{date_text[:4]}/{date_text[4:6]}/{date_text[6:]}"

    try:
        date = parse(date_text)    
    except ValueError:
        pass

    if date is None:
        return None

    if date < datetime.datetime.now():
        date += relativedelta(years=1)

    return date.date()

def parse_tasks(msgs):
    structured = {"task_assignment": {np.inf: defaultdict(list, {})}, "schedule": defaultdict(list, {})}
    current_asignee = None
    current_schedule = None
    interested_dict = None
    last_line = None
    for msg in msgs.split("\n"):
        if msg.startswith("@"):  # handle name
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
            d = weekday_to_date(wd)
            interested_dict[d.strftime(format="%Y/%m/%d")].append(" ".join(msg.split(" ")[1:]))
        elif d:= validate(msg.split(" ")[0]):
            interested_dict[d.strftime(format="%Y/%m/%d")].append(" ".join(msg.split(" ")[1:]))
        elif msg in ["", "\n", None]:  # handle spaces
            pass
        elif interested_dict is not None:
            interested_dict[np.inf].append(msg)
        last_line = msg
    return structured