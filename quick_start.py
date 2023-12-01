import json
import uuid

from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Dict
from typing import List
from typing import Union

from trello_handler import BoardListData

SCOPES = ['https://www.googleapis.com/auth/forms','https://www.googleapis.com/auth/drive']

# 使用service account憑證驗證
credentials = service_account.Credentials.from_service_account_file(
                'credentials.json', scopes=SCOPES)

forms_service = build('forms', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

def add_discord_name_to_trello_name_selection(new_questions: dict, discord_id_to_name_dict: Dict[str, str], trello_name_list: List[str]) -> Dict[str, str]:
    question_id_to_discord_id = {}
    target = new_questions['requests']
    if len(discord_id_to_name_dict) == 0:
        return {}

    target.append({
        'createItem': {
            'item': {
                'title': "",
                'questionGroupItem': {'questions': []}
            },
            "location": {"index": len(target)}
        }
    })
    _target = new_questions['requests'][-1]['createItem']['item']['questionGroupItem']['questions']
    for discord_id, discord_name in discord_id_to_name_dict.items():
        name_id = str(uuid.uuid4()).replace("-", "")[:5]
        question_id_to_discord_id[name_id] = discord_id
        _target.append({
            'questionId': name_id,
            'choiceQuestion': {
                'type': "DROP_DOWN",
                'options': [{'value': trello_name} for trello_name in trello_name_list]
            }
        })
    return question_id_to_discord_id

def add_board_entry_selection(new_questions: dict, board_list_data: BoardListData) -> Dict[str, str]:
    question_id_to_board_id = {}
    target = new_questions['requests']
    for board_id, board_name in board_list_data.board_id_to_name.items():
        name_id = str(uuid.uuid4()).replace("-", "")[:5]
        question_id_to_board_id[name_id] = board_id
        target.append({
            'createItem': {
                'item': {
                    'itemId': name_id,
                    'title': f'選擇 {board_name} 的看板',
                    'questionItem': {
                        'question':{
                            'choiceQuestion': {
                                'type': "DROP_DOWN",
                                'options': [{'value': list_name} for list_name in board_list_data.board_name_to_list_name[board_name]]
                            }
                        }
                    }
                },
                "location": {"index": len(target)},
            }
        })
    return question_id_to_board_id

def add_interested_list_selection(new_questions: dict, board_list_data: BoardListData) -> Dict[str, str]:
    question_id_to_list_id = {}
    target = new_questions['requests']
    for board_name, list_name in board_list_data.board_name_to_list_name.items():
        name_id = str(uuid.uuid4()).replace("-", "")[:5]
        question_id_to_list_id[name_id] = list_name
        target.append({
            'createItem': {
                'item': {
                    'itemId': name_id,
                    'title': f'選擇 {board_name} 的看板',
                    'questionItem': {
                        'question':{
                            'choiceQuestion': {
                                'type': "CHECKBOX",
                                'options': [{'value': list_name} for list_name in list_name]
                            }
                        }
                    }
                },
                "location": {"index": len(target)},
            }
        })
    return question_id_to_list_id

def add_board_keywords(new_questions: dict, board_list_data: BoardListData) -> Dict[str, str]:
    question_id_to_board_id = {}
    target = new_questions['requests']
    for board_id, board_name in board_list_data.board_id_to_name.items():
        name_id = str(uuid.uuid4()).replace("-", "")[:5]
        question_id_to_board_id[name_id] = board_id
        target.append({
            'createItem': {
                'item': {
                    'itemId': name_id,
                    'title': f'請輸入 {board_name} 的關鍵字',
                    'description': "請輸入關鍵字，以逗號分隔，使用\"default\"或留空代表預設看板",
                    'questionItem': {
                        'question':{
                            'textQuestion': {
                                'paragraph': False
                            }
                        }
                    }
                },
                "location": {"index": len(target)},
            }
        })
    return question_id_to_board_id

def create_form(
        guild_id: Union[str, int],
        folder_id: str,
        form_title: str,
        discord_id_to_name_dict: Dict[str, str],
        trello_name_list: List[str],
        board_list_data: BoardListData
        ) -> str:
    # 建立表單物件
    form = {
        'info': {
            'title': form_title,
            'documentTitle': guild_id
        }
    }

    created_form = forms_service.forms().create(body=form).execute()

    NEW_QUESTION = {'requests': [], 'includeFormInResponse': True}
    result_dicts = {}
    # result_dicts["name_matching"] = add_discord_name_to_trello_name_selection(NEW_QUESTION, discord_id_to_name_dict, trello_name_list)
    # input(json.dumps(NEW_QUESTION, indent=4))
    result_dicts["board_entry"] = add_board_entry_selection(NEW_QUESTION, board_list_data)
    result_dicts["interested_lists"] = add_interested_list_selection(NEW_QUESTION, board_list_data)
    result_dicts["board_keywords"] = add_board_keywords(NEW_QUESTION, board_list_data)

    question_setting = (
        forms_service.forms()
        .batchUpdate(formId=created_form["formId"], body=NEW_QUESTION)
        .execute()
    )

    # Prints the result to show the question has been added
    get_result = forms_service.forms().get(formId=created_form["formId"]).execute()
    # print(get_result)


    # 取得建立的表單ID
    form_id = created_form['formId']

    # 將表單新增至指定的Google雲端硬碟資料夾
    file_metadata = {
                'name': form_title,
                'mimeType': 'application/vnd.google-apps.form',
                'parents': [folder_id]
        }

    result = drive_service.files().create(body=file_metadata).execute()
    print(result)

    # print(f'已成功建立表單 "{form_title}" ,表單ID為 {form_id}')
    # print(created_form)
    return form_id, created_form['responderUri']

if __name__ == '__main__':
    guild_id = '12345'
    folder_id = '1IWtm8xae06s91SK2yd_ECRtFy9o6tr5i'
    form_title = '我的第一個表單'


    # class BoardListData:
    # def __init__(self):
    #     self.board_name_to_id = {}
    #     self.board_id_to_name = {}
    #     self.list_name_to_id = {}
    #     self.board_name_to_list_name = {}  # Dict[str, List[str]]
    #     self.list_id_to_name = {}
    bld = BoardListData()
    bld.board_name_to_id = {"board1": "board1_id", "board2": "board2_id"}
    bld.board_id_to_name = {"board1_id": "board1", "board2_id": "board2"}
    bld.list_name_to_id = {"list1": "list1_id", "list2": "list2_id"}
    bld.board_name_to_list_name = {"board1": ["list1", "list2"], "board2": ["list1", "list2"]}
    bld.list_id_to_name = {"list1_id": "list1", "list2_id": "list2"}

    # uri = create_form(guild_id, folder_id, form_title)
    form_id, uri = create_form(
        guild_id,
        folder_id,
        form_title,
        discord_id_to_name_dict={"12908showay": "showay", "09812megan": "megan", "82412tommy": "tommy.good"},
        trello_name_list=["showaykerker", "M", "湯米"],
        board_list_data=bld)
    print(uri)

    input()
    result = forms_service.forms().responses().list(formId=form_id).execute()
    print(result)
    input()
    result = forms_service.forms().responses().list(formId=form_id).execute()
    print(result)