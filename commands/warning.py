import discord
from discord.ext import commands
import asyncio
import aiomysql
import PW
import datetime
import json
import typing
from logs import Logs


def r_u_hojun(ctx):
    return ctx.author.id == 293342265982844928


class Warning(commands.Cog):
    def __init__(self, bot):
        super()
        self.bot = bot
        self.logger = Logs.create_logger(self)
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.set_db())

    async def set_db(self):
        self.conn_pool = await aiomysql.create_pool(
            host="127.0.0.1",
            user=PW.db_user,
            password=PW.db_pw,
            db="litown",
            autocommit=True,
            loop=self.loop,
            minsize=2,
            maxsize=5,
            charset="utf8mb4",
        )

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        else:
            await ctx.send("⚠ 관리자 권한이 필요한 명령어입니다.")

    async def get_user_warn(self, id):
        async with self.conn_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""SELECT * FROM warn WHERE userid = %s""", (str(id)))
                row = await cur.fetchone()
        return row

    async def add_user_warn(self, id, amount, reason, who):
        async with self.conn_pool.acquire() as conn:
            async with conn.cursor() as cur:
                row = await self.get_user_warn(id)
                set_timee = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                if row is None:
                    add = {
                        "total": amount,
                        "warnings": [
                            {
                                "amount": amount,
                                "reason": reason,
                                "when": set_timee,
                                "who": who,
                            }
                        ],
                    }
                    add = json.dumps(add)
                    await cur.execute(
                        """INSERT INTO warn (userid, warnings) VALUES (%s, %s)""",
                        (id, add),
                    )
                else:
                    add = {
                        "amount": amount,
                        "reason": reason,
                        "when": set_timee,
                        "who": who,
                    }

                    change = row[1]
                    change = json.loads(change)
                    change["warnings"].append(add)
                    change["total"] += amount
                    await cur.execute(
                        """UPDATE warn SET warnings=%s WHERE userid=%s""",
                        (json.dumps(change), id),
                    )
        return True

    async def clear_user_warn(self, id):
        async with self.conn_pool.acquire() as conn:
            async with conn.cursor() as cur:
                row = await self.get_user_warn(id)
                if row is None:
                    return False
                else:
                    await cur.execute("""DELETE FROM warn WHERE userid=%s""", (id))
        return True

    @commands.command(name="경고추가", aliases=["경고하기", "경고넣기", "경고주기"])
    async def add_warn(
        self, ctx, users: commands.Greedy[discord.Member], amount, *, reason
    ):
        try:
            amount = int(amount)
        except:
            await ctx.send("잘못된 사용 : `!경고추가 <유저 멘션> <경고 양> <이유>`")
            return

        if amount == 0:
            await ctx.send("⚠️ 경고 양은 0일 수 없습니다.")
            return

        for i in set(users):
            who = "{}#{}".format(ctx.author.name, ctx.author.discriminator)
            if await self.add_user_warn(i.id, amount, reason, who):
                await ctx.send("✅ 성공!")
            else:
                await ctx.send("⚠️ 실패!")

    @add_warn.error
    async def add_warn_error(self, ctx, error):
        self.logger.info(error)
        if isinstance(error, commands.BadArgument) or isinstance(
            error, commands.MissingRequiredArgument
        ):
            await ctx.send("잘못된 사용 : `!경고추가 <유저 멘션> <경고 양> <이유>`")

    @commands.command(name="경고보기", aliases=["경고조회", "경고"])
    async def get_warn(self, ctx, user: discord.Member):
        row = await self.get_user_warn(user.id)
        if row is None:
            await ctx.send("{}님은 경고가 없군요.".format(user.mention))
        else:
            row = json.loads(row[1])
            warnings = row["warnings"]
            total = row["total"]
            details = "현재 {}의 경고는 **{}%**입니다.\n\n".format(user.mention, total)

            for i in range(len(warnings)):
                now_warn = warnings[i]
                amount = now_warn["amount"]
                if amount > 0:
                    amount = "+" + str(amount)
                else:
                    amount = str(amount)
                details += "`[{}] {}에 '{}'로 경고가 {} 되었습니다. (by {})`\n".format(
                    i + 1,
                    now_warn["when"],
                    now_warn["reason"],
                    amount,
                    now_warn["who"],
                )

            await ctx.send(details)

    @get_warn.error
    async def get_warn_error(self, ctx, error):
        self.logger.info(error)
        if isinstance(error, commands.BadArgument) or isinstance(
            error, commands.MissingRequiredArgument
        ):
            await ctx.send("잘못된 사용 : `!경고보기 <유저 멘션>`")

    @commands.command(name="경고리셋", aliases=["경고초기화", "경고날리기"])
    @commands.check(r_u_hojun)
    async def clear_warn(self, ctx, users: commands.Greedy[discord.Member]):
        for i in set(users):
            user = ctx.message.mentions[0]
            if await self.clear_user_warn(i.id):
                await ctx.send("✅ 성공!")
            else:
                await ctx.send("⚠️ 실패!")

    @clear_warn.error
    async def clear_error(self, ctx, error):
        self.logger.info(error)
        if isinstance(error, commands.BadArgument) or isinstance(
            error, commands.MissingRequiredArgument
        ):
            await ctx.send("잘못된 사용 : `!경고리셋 <유저 멘션>`")

        if isinstance(error, commands.CheckFailure):
            await ctx.send("~~MEE6 랭크 1위만 사용 가능한 명령어입니다.~~")

    @commands.command(name="reload")
    async def reload(self, ctx, module):
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
            await ctx.send("✅")
        except Exception as error:
            await ctx.send("실패 {}".format(error))


def setup(bot):
    bot.add_cog(Warning(bot))
