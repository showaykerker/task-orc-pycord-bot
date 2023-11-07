from typing import Union, List, Optional, Dict
import datetime

import numpy as np
from trello import TrelloClient
from trello.board import Board
from trello.card import Card

class DateCard(Card):
    def __init__(self, card: Card):
        self._card = card
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

    def to_list_of_dict(self) -> List[dict]:
        return [{
            "board": c.board,
            "list": c.list,
            "title": c.title,
            "due": c.due,
            "members": c.members
        } for c in self._c]

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

    def get_undone(self, inp: Union[str, int, TrelloClient]) -> Optional[FilteredCards]:
        trello = self._parse_input(inp)
        if trello is None: return
        cards = FilteredCards()
        for card in trello.search(
                "-label:header is:open sort:due -list:done -list:ideas -list:resources",
                models=["cards",]):
            cards.append(card)
        # for board in trello.list_boards():
        #     for c in board.open_cards():
        #         if c
        #         cards.append(card)
        cards.sort()
        return cards

    def __getitem__(self, guild_id: Union[str, int]) -> TrelloClient:
        return self._clients.get(str(guild_id))