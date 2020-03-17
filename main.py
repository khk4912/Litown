import discord
from discord.ext import commands
import TOKEN
import logging
import PW
from logs import Logs
import sys


class Litown(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=["!"])
        self.logger = Logs.create_logger(self)
        self.main_logger = Logs.main_logger()
        for i in TOKEN.initial_extensions:
            self.load_extension(i)

    async def on_ready(self):
        self.logger.info("Bot Ready.")

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    # async def on_command_error(self, ctx, error):
    #     if isinstance(error, commands.BadArgument):
    #         await ctx.send("❌ 잘못된 사용법, `!도움말`로 명령어 확인 후 재시도하세요.")


bot = Litown()
bot.remove_command("help")
bot.run(TOKEN.bot_token)
