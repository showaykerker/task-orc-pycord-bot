from typing import Union, List
import datetime

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
            return self._due + datetime.timedelta(hours=8)
        return None
    
    def stamp(self) -> float:
        if self._due:
            return self._due.timestamp()
        else:
            return (datetime.datetime.max - datetime.timedelta(days=1)).timestamp()


class FilteredCards:
    def __init__(self):
        self._c = []

    def append(self, card: Card):
        self._c.append(DateCard(card))

    def sort(self):
        self._c.sort(key=lambda x: x.stamp())



class TrelloHandler:
    def __init__(self):
        self._clients = {} # guild_id(str): TrelloClient
    def _parse_input(self, inp: Union[str, int, TrelloClient]) -> TrelloClient:
        if isinstance(inp, TrelloClient):
            return inp
        else:
            return self._clients.get(str(inp))

    def add_client(self, guild_id: Union[str, int], key: str, token: str) -> None:
        self._clients[str(guild_id)] = TrelloClient(
            api_key=key,
            api_secret=token)

    def contains_guild(self, guild_id: Union[str, int]) -> bool:
        return str(guild_id) in self._clients.keys()

    def get_boards(self, guild_id: Union[str, int]) -> List[Board]:
        return self._clients[str(guild_id)].list_boards()

    def get_undone(self, inp: Union[str, int, TrelloClient]) -> Optional[FilteredCards]:
        trello = self._parse_input(inp)
        print("get_undone 1")
        if trello is None: return
        print("get_undone 2")
        cards = FilteredCards()
        for card in trello.search(
                "-label:header is:open sort:due -list:done -list:ideas -list:resources",
                models=["cards",]):
            print(card)
            cards.append(card)
        cards.sort()
        return cards

    def __getitem__(self, guild_id: Union[str, int]) -> TrelloClient:
        return self._clients.get(str(guild_id))