from typing import Optional, Tuple, Union, Dict, List
import json
import pandas as pd
import sqlite3

from discord import ApplicationContext
from ezcord.sql import DBHandler
from encryption import encrypt, decrypt

class MemberData:
    def __init__(self, guild_id: str, name: str, discord_id: str, trello_id: Optional[str] = "") -> None:
        self.guild_id = guild_id
        self.name = name
        self.discord_id = discord_id
        self.trello_id = trello_id

def error_handler(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except sqlite3.IntegrityError as e:
            print(f"\033[1;31m[TaskOrcDB] WARNING: {e}\033[0m")
            return None
        except sqlite3.OperationalError as e:
            print(f"\033[1;31m[TaskOrcDB] WARNING: {e}\033[0m")
            return None
    return wrapper

class TrelloSettings:
    def __init__(self, rows: list[tuple]) -> None:
        self.list_name_not_to_trace = []
        for row in rows:
            if row[1] == "trello_no_trace_list_name":
                self.list_name_not_to_trace.append(row[2])

    def __str__(self) -> str:
        return "<TrelloSettings>\n" +\
            "list_name_not_to_trace: \n"\
            f"{json.dumps(self.list_name_not_to_trace, indent=4, ensure_ascii=False)}\n"


class TaskOrcDB(DBHandler):

    def __init__(self) -> None:
        """Initialize the database handler."""
        super().__init__("taskorc.db")
        # self.member_data = {}  # {"guild_id": [MemberData, ]}

    async def setup(self) -> None:
        """Set up the database schema."""
        async with self.start() as db:
            await db.exec(
                "CREATE TABLE IF NOT EXISTS Member "\
                "(id INTEGER PRIMARY KEY, guild_id TEXT, name TEXT, discord_id TEXT, trello_id TEXT)")
            await db.exec(
                "CREATE TABLE IF NOT EXISTS TrelloData"\
                "(guild_id TEXT, item TEXT, value TEXT, value2 TEXT)")

    # Member related

    async def insert_member(self, member: MemberData) -> None:
        """Insert a new member record into the database."""
        assert isinstance(member, MemberData)
        assert member.guild_id
        assert member.discord_id

        async with self.start() as db:
            row = await db.exec("SELECT * FROM Member WHERE guild_id = ? AND discord_id = ?",
                member.guild_id, member.discord_id)
            row = await row.fetchone()
            if row:
                await db.exec(
                    "UPDATE Member SET name = ? WHERE guild_id = ? AND discord_id = ?",
                    member.name, member.guild_id, member.discord_id
                )
            else:
                await db.exec(
                    "INSERT INTO Member (guild_id, name, discord_id, trello_id) VALUES (?, ?, ?, ?)",
                    member.guild_id, member.name, member.discord_id, member.trello_id
                )

    async def update_trello_id(self, guild_id: str, discord_id: str, trello_id: str) -> None:
        """Add a Trello ID to an existing member record."""
        async with self.start() as db:
            row = await db.exec("SELECT * FROM Member WHERE guild_id = ? AND discord_id = ?",
                guild_id, discord_id)
            row = await row.fetchone()
            if row:
                await db.exec(
                    "UPDATE Member SET trello_id = ? WHERE guild_id = ? AND discord_id = ?",
                    trello_id, guild_id, discord_id
                )
            else:
                print("\n\033[1;31m[TaskOrcDB] WARNING"\
                    "Unknown member with "\
                    f"guild_id \033[3m{guild_id}'\033[1;31m and "\
                    f"discord_id \033[3m'{discord_id}'\033[1;31m. "\
                    "Unable to update with "\
                    f"trello_id \033[3m'{trello_id}'\033[1;31m. "\
                    "Skip.\033[0m\n")

    async def configure_guild_members(self, ctx:ApplicationContext) -> None:
        member_list = []
        async for member in ctx.guild.fetch_members():
            # skip robot members
            if member.bot:
                continue
            member_list.append({
                "name": member.display_name,
                "discord_id": member.id
            })
        await self.set_member_data(ctx.guild_id, member_list)

    @error_handler
    async def get_member_data(self, guild_id: Union[str, int]) -> pd.DataFrame:
        """Retrieve all member data as a Pandas DataFrame."""
        async with self.start() as db:
            rows = await db.exec("SELECT * FROM Member WHERE guild_id = ?",
                guild_id
            )
            rows = await rows.fetchall()
            return pd.DataFrame(
                rows, columns=["id", "guild_id", "name", "discord_id", "trello_id"])

    async def get_discord_name_to_trello_id_dict(self, guild_id: Union[str, int], member_data: pd.DataFrame=None) -> Dict[str, str]:
        """Retrieve member name from Trello ID."""
        if member_data is None:
            member_data = await self.get_member_data(guild_id)
        return dict(zip(member_data["name"], member_data["trello_id"]))

    async def get_trello_id_to_discord_name_dict(self, guild_id: Union[str, int]) -> Dict[str, str]:
        """Retrieve member name from Trello ID."""
        data = await self.get_member_data(guild_id)
        return dict(zip(data["trello_id"], data["name"]))

    async def get_trello_id_from_discord_id(self, guild_id: Union[str, int], discord_id: str) -> str:
        """Retrieve Trello ID from Discord ID."""
        async with self.start() as db:
            rows = await db.exec("SELECT trello_id FROM Member WHERE guild_id = ? AND discord_id = ?",
                guild_id, discord_id
            )
            rows = await rows.fetchone()
            return None if rows is None else rows[0]

    async def set_member_data(self, guild_id: str, member_list: list[dict]) -> None:
        """Set member data to the database."""
        async with self.start() as db:
            for member in member_list:
                await self.insert_member(
                    MemberData(guild_id, member["name"], member["discord_id"]))

    # Trello related
    async def set_trello_key_token(self, guild_id: str, key: str, token: str) -> bool:
        """Save Guild's Trello key and token to the database."""

        key, token = encrypt(key), encrypt(token)

        async with self.start() as db:
            exists = await db.exec(
                "SELECT EXISTS(SELECT 1 FROM TrelloData WHERE guild_id = ?)", guild_id)
            exists = await exists.fetchone()
            print(f"[DBH] Exists = {exists}")
            if exists[0]:
                await db.exec(
                    "UPDATE TrelloData SET value = ? WHERE guild_id = ? AND item = ?",
                    key, guild_id, "key"
                )
                await db.exec(
                    "UPDATE TrelloData SET value = ? WHERE guild_id = ? AND item = ?",
                    token, guild_id, "token"
                )
                return True
            else:
                await db.exec(
                    "INSERT INTO TrelloData (guild_id, item, value) VALUES (?, ?, ?)",
                    guild_id, "key", key
                )
                await db.exec(
                    "INSERT INTO TrelloData (guild_id, item, value) VALUES (?, ?, ?)",
                    guild_id, "token", token
                )
                return False

    @error_handler
    async def get_trello_key_token(self, guild_id: str) -> Tuple[str, str]:
        """Retrieve Guild's Trello key and token from the database."""
        async with self.start() as db:
            # get key and secret as strings
            key = await db.exec(
                "SELECT value FROM TrelloData WHERE guild_id = ? AND item = ?",
                guild_id, "key"
            )
            token = await db.exec(
                "SELECT value FROM TrelloData WHERE guild_id = ? AND item = ?",
                guild_id, "token"
            )
            key = await key.fetchone()
            token = await token.fetchone()
            if key is None or token is None:
                return None, None
            return decrypt(key[0]), decrypt(token[0])


    async def set_trello_traced_list_name_not_to_trace(self, guild_id: str, trello_no_trace_list_name: List[str]) -> None:
        """Save Trello traced list ID to the database."""
        async with self.start() as db:
            exists = await db.exec(
                "SELECT EXISTS(SELECT * FROM TrelloData WHERE guild_id = ? AND item = ?)", guild_id, "trello_no_trace_list_name")
            exists = await exists.fetchall()
            if exists:
                await db.exec(
                    "DELETE FROM TrelloData WHERE guild_id = ? AND item = ?",
                    guild_id, "trello_no_trace_list_name"
                )
            for tid in trello_no_trace_list_name:
                await db.exec(
                    "INSERT INTO TrelloData (guild_id, item, value) VALUES (?, ?, ?)",
                    guild_id, "trello_no_trace_list_name", tid
                )

    async def get_trello_settings(self, guild_id: Union[str, int]) -> TrelloSettings:
        """Retrieve Trello settings from the database."""
        async with self.start() as db:
            rows = await db.exec("SELECT * FROM TrelloData WHERE guild_id = ? AND item = ?",
                guild_id, "trello_no_trace_list_name"
            )
            rows = await rows.fetchall()
            return TrelloSettings(rows)


async def test():

    db = TaskOrcDB()

    await db.setup()

    # Test member insertion
    test_member = MemberData("guild1", "John", "didJohn")
    await db.insert_member(test_member)
    test_member = MemberData("guild1", "showay", "didshoway")
    await db.insert_member(test_member)
    test_member = MemberData("guild1", "kerker", "didkerker", "trelloidkerker")
    await db.insert_member(test_member)
    test_member = MemberData("guild2", "heyhey", "didheyhey")
    await db.insert_member(test_member)

    df = await db.get_member_data()
    print("Before: ")
    input(df)

    # Test trello id addition
    await db.update_trello_id("guild1", "didJohn", "trelloid123")
    await db.update_trello_id("guild2", "didheyhey", "trelloidheyhey")
    await db.update_trello_id("guild2123", "didheyhey", "trelloidheyhey")

    # Test get data
    df = await db.get_member_data()
    print("\n\nAfter: ")
    print(df)


if __name__ == '__main__':
    import asyncio
    asyncio.run(test())