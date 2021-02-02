import random
import re
import typing as t
from urllib.parse import quote_plus

from discord import Embed
from discord.ext import commands
from discord.ext.commands import BucketType, Context

from bot import constants
from bot.constants import Categories, Channels, Colours, ERROR_REPLIES, Roles, WHITELISTED_CHANNELS
from bot.utils.decorators import with_role

ERROR_MESSAGE = f"""
Unknown cheat sheet. Please try to reformulate your query.

**Examples**:
```md
{constants.Client.prefix}cht read json
{constants.Client.prefix}cht hello world
{constants.Client.prefix}cht lambda
```
If the problem persists send a message in <#{Channels.dev_contrib}>
"""

URL = 'https://cheat.sh/python/{search}'
ESCAPE_TT = str.maketrans({"`": "\\`"})
ANSI_RE = re.compile(r"\x1b\[.*?m")


class CheatSheet(commands.Cog):
    """Commands that sends a result of a cht.sh search in code blocks."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def fmt_error_embed() -> Embed:
        """
        Format the Error Embed.

        If the cht.sh search returned 404, overwrite it to send a custom error embed.
        link -> https://github.com/chubin/cheat.sh/issues/198
        """
        embed = Embed(
            title=random.choice(ERROR_REPLIES),
            description=ERROR_MESSAGE,
            colour=Colours.soft_red
        )
        return embed

    def result_fmt(self, url: str, body_text: str) -> t.Tuple[bool, t.Union[str, Embed]]:
        """Format Result."""
        if body_text.startswith("#  404 NOT FOUND"):
            embed = self.fmt_error_embed()
            return True, embed

        body_space = min(1986 - len(url), 1000)

        if len(body_text) > body_space:
            description = f"**Result Of cht.sh**\n" \
                          f"```python\n{body_text[:body_space]}\n" \
                          f"... (truncated - too many lines)```\n" \
                          f"Full results: {url} "
        else:
            description = f"**Result Of cht.sh**\n" \
                          f"```python\n{body_text}```\n" \
                          f"{url}"
        return False, description

    @commands.command(
        name="cheat",
        aliases=("cht.sh", "cheatsheet", "cheat-sheet", "cht"),
    )
    @commands.cooldown(1, 10, BucketType.user)
    @with_role(Roles.everyone)
    async def cheat_sheet(self, ctx: Context, *search_terms: str) -> None:
        """
        Search cheat.sh.

        Gets a post from https://cheat.sh/python/ by default.
        Usage:
        --> .cht read json
        """
        if not (
            ctx.channel.category.id == Categories.help_in_use
            or ctx.channel.id in WHITELISTED_CHANNELS
        ):
            return

        async with self.bot.http_session.get(
                URL.format(search=quote_plus(" ".join(search_terms)))
        ) as response:
            result = ANSI_RE.sub("", await response.text()).translate(ESCAPE_TT)

        is_embed, description = self.result_fmt(
            URL.format(search=quote_plus(" ".join(search_terms))),
            result
        )
        if is_embed:
            await ctx.send(embed=description)
        else:
            await ctx.send(content=description)


def setup(bot: commands.Bot) -> None:
    """Load the CheatSheet cog."""
    bot.add_cog(CheatSheet(bot))
