from typing import Union, List, Optional, Dict, Tuple
import datetime
import math
import json

import numpy as np
from trello import TrelloClient
from trello.board import Board
from trello.card import Card

class BoardListData:
    def __init__(self):
        self.board_name_to_id = {}
        self.list_name_to_id = {}
        self.board_name_to_list_name = {}  # Dict[str, List[str]]

    def __len__(self):
        return len(self.list_name_to_id)

    def __str__(self):
        return "<BoardListData>\n" +\
            "board_name_to_id:\n" +\
            json.dumps(self.board_name_to_id, indent=4, ensure_ascii=False) + "\n" +\
            "list_name_to_id:\n" +\
            json.dumps(self.list_name_to_id, indent=4, ensure_ascii=False) + "\n" +\
            "board_name_to_list_name:\n" +\
            json.dumps(self.board_name_to_list_name, indent=4, ensure_ascii=False) + "\n"

class DateCard(Card):
    def __init__(self, card: Card):
        self._card = card
        self.url = card.short_url
        self.board = card.board_id
        self.list = card.get_list()
        self.title = card.name
        self.members = card.member_id
        self._due = card.due_date

    @property
    def due(self):
        if self._due:
            return (self._due + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        return None

    def stamp(self) -> float:
        if self._due:
            return self._due.timestamp()
        else:
            return np.inf


class FilteredCards:
    def __init__(self):
        self._c = []

    def append(self, card: Card):
        self._c.append(DateCard(card))

    def sort(self):
        self._c.sort(key=lambda x: x.stamp())

    def to_list_of_dict(
            self,
            trello_id_to_discord_name: Dict[str, str],
            member_max_length: int=None) -> List[dict]:
        return_list = []
        for c in self._c:
            ms = len(c.members)
            member_strings = []
            for i_m, member in enumerate(c.members):
                size_limit = np.inf if member_max_length is None else\
                    math.floor((member_max_length - (ms-1)) / ms)
                member_str = trello_id_to_discord_name.get(member) or member
                if len(member_str) > size_limit:
                    member_str = member_str[:size_limit-1] + "."
                member_strings.append(member_str)
            member_strings = "|".join(member_strings)
            return_list.append({
                "url": c.url,
                "board": c.board,
                "list": c.list,
                "title": c.title,
                "due": c.due,
                "members": member_strings
            })
        return return_list

    def __len__(self):
        return len(self._c)


class TrelloHandler:

    def __init__(self):
        self._clients = {}  # guild_id(str): TrelloClient
        self._board_id_to_name = {}  # guild_id(str): {board_id(str): board_name}

    def _parse_input(self, inp: Union[str, int, TrelloClient]) -> TrelloClient:
        if isinstance(inp, TrelloClient):
            return inp
        else:
            return self._clients.get(str(inp))

    def add_client(self, guild_id: Union[str, int], key: str, token: str) -> None:
        self._clients[str(guild_id)] = TrelloClient(
            api_key=key,
            api_secret=token)
        self.update_board_id_to_name(guild_id)

    def remove_client(self, guild_id: Union[str, int]) -> None:
        if str(guild_id) in self._clients.keys():
            del self._clients[str(guild_id)]
        if str(guild_id) in self._board_id_to_name.keys():
            self._board_id_to_name[str(guild_id)] = {}

    def update_board_id_to_name(self, guild_id: Union[str, int]) -> None:
        trello = self._clients[str(guild_id)]
        if trello is None: return
        self._board_id_to_name[str(guild_id)] = {}
        all_boards = trello.list_boards()
        for b in all_boards:
            self._board_id_to_name[str(guild_id)][b.id] = b.name

    def get_board_names(self, guild_id: Union[str, int]) -> dict:
        self.update_board_id_to_name(guild_id)
        guild_boards = self._board_id_to_name.get(str(guild_id))
        return guild_boards if guild_boards else {}

    def contains_guild(self, guild_id: Union[str, int]) -> bool:
        return str(guild_id) in self._clients.keys()

    async def get_members(self, inp: Union[str, int, TrelloClient]) -> Dict[str, str]:
        trello = self._parse_input(inp)
        if trello is None: return

        all_boards = trello.list_boards()
        member_id_to_name_dict = {}
        for board in all_boards:
            for m in board.all_members():
                member_id_to_name_dict[m.id] = m.full_name
        return member_id_to_name_dict

    def get_boards(self, guild_id: Union[str, int]) -> List[Board]:
        return self._clients[str(guild_id)].list_boards()

    def get_undone(self, inp: Union[str, int, TrelloClient], trello_id: str=None) -> Optional[FilteredCards]:
        trello = self._parse_input(inp)
        if trello is None: return
        cards = FilteredCards()
        query = "-label:header is:open -list:ideas -list:resources -due:complete sort:due"
        if trello_id: query += f" member:{trello_id}"
        for card in trello.search(query, models=["cards",], cards_limit=1000):
            cards.append(card)
        return cards

    async def get_board_list_data(self, guild_id: Union[str, int]) -> BoardListData:
        board_list_data = BoardListData()
        trello = self._clients[str(guild_id)]
        if trello is None: return board_list_data

        all_boards = trello.list_boards()
        for board in all_boards:
            board_list_data.board_name_to_id[board.name] = board.id
            board_list_data.board_name_to_list_name[board.name] = []
            for l in board.list_lists():
                board_list_data.list_name_to_id[l.name] = l.id
                board_list_data.board_name_to_list_name[board.name].append(l.name)
        return board_list_data

    def __getitem__(self, guild_id: Union[str, int]) -> TrelloClient:
        return self._clients.get(str(guild_id))