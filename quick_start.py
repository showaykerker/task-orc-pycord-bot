from typing import Union
from googleapiclient.discovery import build
from google.oauth2 import service_account

from trello_handler import BoardListData

SCOPES = ['https://www.googleapis.com/auth/forms','https://www.googleapis.com/auth/drive']

# 使用service account憑證驗證
credentials = service_account.Credentials.from_service_account_file(
                'credentials.json', scopes=SCOPES)

forms_service = build('forms', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

def create_form(
        guild_id: Union[str, int],
        folder_id: str,
        form_title: str,
        discord_name_list: list,
        trello_name_list: list,
        board_list_data: BoardListData
        ) -> str:
    # 建立表單物件
    form = {
        'info': {
            'title': form_title,
            'documentTitle': guild_id
        }
    }

    # 在Google Forms上新增表單
    created_form = forms_service.forms().create(body=form).execute()


    # Request body to add a multiple-choice question
    NEW_QUESTION = {
        'requests':
        [
            {
                'createItem': {
                    'item': {
                        'title': '國家',
                        'questionItem': {
                            'question':{
                                'choiceQuestion': {
                                    'type': "DROP_DOWN",
                                    'options': [
                                        {'value': '台灣'},
                                        {'value': '美國'},
                                        {'value': '日本'}
                                    ]
                                }
                            }
                        }
                    },
                    "location": {"index": 0},
                }
            }
        ]
    }
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

    drive_service.files().create(body=file_metadata).execute()

    # print(f'已成功建立表單 "{form_title}" ,表單ID為 {form_id}')
    # print(created_form)
    return created_form['responderUri']

if __name__ == '__main__':
    guild_id = '12345'
    folder_id = '1IWtm8xae06s91SK2yd_ECRtFy9o6tr5i'
    form_title = '我的第一個表單'

    # uri = create_form(guild_id, folder_id, form_title)
    uri = create_form(
        guild_id,
        folder_id,
        form_title,
        discord_name_list=[],
        trello_name_list=[],
        board_list_data=BoardListData())
    print(uri)