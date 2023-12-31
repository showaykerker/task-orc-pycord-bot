import datetime
import json
import math

from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np

import ezcord
from discord import ApplicationContext
from trello import TrelloClient
from trello.board import Board
from trello.card import Card
from trello.trellolist import List as TrelloList

class BoardListData:
    def __init__(self):
        self.board_name_to_id = {}
        self.board_id_to_name = {}
        self.list_name_to_id = {}
        self.board_name_to_list_name = {}  # Dict[str, List[str]]
        self.list_id_to_name = {}

    def __len__(self):
        return len(self.list_name_to_id)

    def __str__(self):
        return "<BoardListData>\n"\
            "board_name_to_id:\n"\
            f"{json.dumps(self.board_name_to_id, indent=4, ensure_ascii=False)}\n"\
            "board_id_to_name:\n"\
            f"{json.dumps(self.board_id_to_name, indent=4, ensure_ascii=False)}\n"\
            "list_name_to_id:\n"\
            f"{json.dumps(self.list_name_to_id, indent=4, ensure_ascii=False)}\n"\
            "board_name_to_list_name:\n"\
            f"{json.dumps(self.board_name_to_list_name, indent=4, ensure_ascii=False)}\n"\
            "list_id_to_name:\n"\
            f"{json.dumps(self.list_id_to_name, indent=4, ensure_ascii=False)}"

class TrelloDummyAssign:
    def __init__(self, assignee_id: str):
        self.id = assignee_id

class DateCard(Card):
    def __init__(
            self,
            card: Optional[Card]=None,
            due: Optional[datetime.datetime]=None,
            board: Optional[str]=None,
            t_list: Optional[str]=None,
            title: Optional[str]=None,
            members: Optional[List[str]]=None):
        if card:
            self._card = card
            self.url = card.short_url
            self.board = card.board_id
            self.list = card.get_list()
            self.title = card.name
            self.members = card.member_id
            self._due = card.due_date
        else:
            self._card = None
            self.url = None
            self.board = board
            self.list = t_list
            self.title = title
            self.members = members
            self._due = due


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

no_trello_error_msg = lambda ctx: ezcord.emb.error(
    ctx, "No Trello configuration found. Use /configure_trello First.")

async def get_trello_instance(
        cog_class: ezcord.Cog,
        ctx: Union[ApplicationContext,int,str]) -> TrelloClient:
    if isinstance(ctx, ApplicationContext):
        gid = ctx.guild_id
    else:
        gid = ctx

    if not cog_class.bot.trello.contains_guild(gid):
        key, token = await cog_class.bot.db.get_trello_key_token(gid)
        if key is None or token is None:
            if isinstance(ctx, ApplicationContext):
                await no_trello_error_msg(ctx)
            return
        await cog_class.bot.trello.add_client(gid, key, token)
    trello = cog_class.bot.trello[gid]
    if trello:
        return trello
    if isinstance(ctx, ApplicationContext):
        await no_trello_error_msg(ctx)
    return

class FilteredCards:
    def __init__(self):
        self._c = []

    def append(self, card: Card) -> None:
        self._c.append(DateCard(card))

    def plain_append(self, card: DateCard) -> None:
        self._c.append(card)

    def sort(self):
        self._c.sort(key=lambda x: x.stamp())

    def to_list_of_dict(
            self,
            trello_id_to_discord_name: Optional[Dict[str, str]]={},
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

    async def add_client(self, guild_id: Union[str, int], key: str, token: str) -> None:
        self._clients[str(guild_id)] = TrelloClient(
            api_key=key,
            api_secret=token)
        await self.update_board_id_to_name(guild_id)

    def remove_client(self, guild_id: Union[str, int]) -> None:
        if str(guild_id) in self._clients.keys():
            del self._clients[str(guild_id)]
        if str(guild_id) in self._board_id_to_name.keys():
            self._board_id_to_name[str(guild_id)] = {}

    async def update_board_id_to_name(self, guild_id: Union[str, int]) -> None:
        trello = self._clients[str(guild_id)]
        if trello is None: return
        self._board_id_to_name[str(guild_id)] = {}
        all_boards = trello.list_boards()
        for b in all_boards:
            self._board_id_to_name[str(guild_id)][b.id] = b.name

    async def get_board_names(self, guild_id: Union[str, int]) -> dict:
        await self.update_board_id_to_name(guild_id)
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

    async def get_boards(self, guild_id: Union[str, int]) -> List[Board]:
        return self._clients[str(guild_id)].list_boards()

    async def get_undone(
            self,
            inp: Union[str, int, TrelloClient],
            trello_id: str=None,
            list_name_not_to_trace: List[str] = []) -> Optional[FilteredCards]:
        trello = self._parse_input(inp)
        if trello is None: return
        cards = FilteredCards()
        query = "is:open -due:complete sort:due -label:header"
        if trello_id: query += f" member:{trello_id}"
        for name in list_name_not_to_trace:
            query += f" -list:\"{name}\""
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
            board_list_data.board_id_to_name[board.id] = board.name
            board_list_data.board_name_to_list_name[board.name] = []
            for l in board.list_lists():
                if l.closed: continue
                board_list_data.list_name_to_id[l.name] = l.id
                board_list_data.list_id_to_name[l.id] = l.name
                board_list_data.board_name_to_list_name[board.name].append(l.name)
        return board_list_data

    async def add_card(self, trello: TrelloClient, t_list: TrelloList, card: Dict) -> Card:
        try:
            return t_list.add_card(
                card["name"],
                desc=None,
                labels=None,
                due=card["due"],
                source=None,
                position='top',
                assign=card["assign"])
        except Exception as e:
            print(e)
            return None

    async def add_cards(
            self,
            inp: Union[str, int, TrelloClient],
            board_ids: List[str],
            list_ids: List[str],
            names: List[str],
            dues: List[Optional[str]],
            assigns: List[Optional[List[TrelloDummyAssign]]]=[],
            serials: List[int]=[]) -> Dict[str, Card]:
        trello = self._parse_input(inp)
        if trello is None: return
        request_dict = {}  # {"board_id": {"list_id": [{"name": name, "due": due, "assign": assign, "serial": serial}, ...], ...}, ...}
        for i, (bid, lid, n, due, assign, serial) in enumerate(zip(board_ids, list_ids, names, dues, assigns, serials)):
            due = f"{due}T15:59:59.000Z" if due else ""
            if bid not in request_dict.keys(): request_dict[bid] = {}
            if lid not in request_dict[bid].keys(): request_dict[bid][lid] = []
            request_dict[bid][lid].append({"name": n, "due": due, "assign": assign, "serial": serial})
        created_cards = {}
        for bid, lids in request_dict.items():
            board = trello.get_board(bid)
            for lid, cards in lids.items():
                t_list = board.get_list(lid)
                for card_dict in cards:
                    created = await self.add_card(trello, t_list, card_dict)
                    created_cards[card_dict["serial"]] = created
        return created_cards


    def __getitem__(self, guild_id: Union[str, int]) -> TrelloClient:
        return self._clients.get(str(guild_id))