from typing import Optional
import pandas as pd

from ezcord.sql import DBHandler

class MemberData:
    def __init__(self, guild_id: str, name: str, discord_id: str, trello_id: Optional[str] = "") -> None:
        self.guild_id = guild_id
        self.name = name
        self.discord_id = discord_id
        self.trello_id = trello_id

class TaskOrcDB(DBHandler):

    def __init__(self) -> None:
        """Initialize the database handler."""
        super().__init__("taskorc.db")

    async def setup(self) -> None:
        """Set up the database schema."""
        async with self.start() as db:
            await db.exec(
                "CREATE TABLE IF NOT EXISTS Member "
                "(id INTEGER PRIMARY KEY, guild_id TEXT, name TEXT, discord_id TEXT, trello_id TEXT)")

    async def insert_member(self, member: MemberData) -> None:
        """Insert a new member record into the database."""
        assert isinstance(member, MemberData)
        assert member.guild_id
        assert member.name

        async with self.start() as db:
            row = await db.exec("SELECT * FROM Member WHERE guild_id = ? AND discord_id = ?",
                member.guild_id, member.discord_id)
            row = await row.fetchone()
            if row:
                print(f"\033[0;33m[TaskOrcDB] WARNING"\
                    f"Member \033[3m'{member.name}'\033[0;33m with "\
                    f"guild_id \033[3m'{member.guild_id}'\033[0;33m and "\
                    f"discord_id \033[3m'{member.discord_id}'\033[0;33m "\
                    "already exists. Skip.\033[0m")
                return
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

    async def get_member_data(self, guild_id:Optional[str]="") -> pd.DataFrame:
        """Retrieve all member data as a Pandas DataFrame."""
        async with self.start() as db:
            if guild_id:
                rows = await db.exec("SELECT * FROM Member WHERE guild_id = ?",
                    guild_id
                )
            else:
                rows = await db.exec("SELECT * FROM Member")
            rows = await rows.fetchall()
            return pd.DataFrame(
                rows, columns=["id", "guild_id", "name", "discord_id", "trello_id"])


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