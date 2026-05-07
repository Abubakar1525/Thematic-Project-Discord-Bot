import discord
from discord.ext import commands
from database import init_db, add_warning, get_warnings, clear_warnings, add_ban
from filter_service import contains_banned_word
import asyncio
from datetime import timedelta

# Bot configuration
TOKEN = ""
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if contains_banned_word(message.content):
        await message.delete()
        add_warning(message.author.id, bot.user.id, "Automatic: banned word used")
        rows = get_warnings(message.author.id)
        count = len(rows)
        try:
            await message.author.send(f"Your message in **{message.guild.name}** was removed for using banned words. You now have {count} warning(s).")
        except discord.Forbidden:
            pass
        mod_log = discord.utils.get(message.guild.text_channels, name="mod-log")
        if mod_log:
            await mod_log.send(embed=mod_embed(f"Auto-Warn (#{count})", bot.user, message.author, "Banned word used"))
        return
    await bot.process_commands(message)


def mod_embed(action, moderator, user, reason=None, color=discord.Color.red()):
    embed = discord.Embed(title="Moderation Action", color=color)
    embed.add_field(name="Action", value=action, inline=False)
    embed.add_field(name="User", value=str(user), inline=True)
    embed.add_field(name="Moderator", value=str(moderator), inline=True)
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed



@bot.command()
async def ping(ctx):
    await ctx.send("pong")



# --- Kick ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(embed=mod_embed("Kick", ctx.author, member, reason))


# --- Ban ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    add_ban(member.id, ctx.author.id, reason)
    await ctx.send(embed=mod_embed("Ban", ctx.author, member, reason))


# --- Unban ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, user: str):
    banned_users = [entry async for entry in ctx.guild.bans()]
    name, discriminator = user.split("#") if "#" in user else (user, None)

    for ban_entry in banned_users:
        if discriminator:
            if ban_entry.user.name == name and ban_entry.user.discriminator == discriminator:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"Unbanned {ban_entry.user.mention}")
                return
        else:
            if ban_entry.user.name == name:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"Unbanned {ban_entry.user.mention}")
                return

    await ctx.send("User not found in ban list.")


# --- Timeout (mute) ---
@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(embed=mod_embed(f"Timeout ({minutes} min)", ctx.author, member, reason))


# --- Remove timeout ---
@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(embed=mod_embed("Remove Timeout", ctx.author, member))


# --- Purge messages ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = None):
    if amount is None:
        await ctx.send("Please provide a valid number.")
        return
    if amount > 100:
        await ctx.send("Max 100 messages.")
        return
    if amount < 1:
        await ctx.send("Please provide a valid number.")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"Deleted {len(deleted) - 1} messages.")


# --- Warn ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    add_warning(member.id, ctx.author.id, reason)
    rows = get_warnings(member.id)
    count = len(rows)
    await ctx.send(embed=mod_embed(f"Warn (#{count})", ctx.author, member, reason))
    mod_log = discord.utils.get(ctx.guild.text_channels, name="mod-log")
    if mod_log:
        await mod_log.send(embed=mod_embed(f"Warn (#{count})", ctx.author, member, reason))


@bot.command()
@commands.has_permissions(manage_messages=True)
async def warnings(ctx, member: discord.Member):
    rows = get_warnings(member.id)
    if not rows:
        await ctx.send(f"{member.mention} has no warnings.")
        return
    warn_text = "\n".join(f"{reason} ({timestamp[:10]})" for reason, timestamp in rows)
    await ctx.send(f"Warnings for {member.display_name}:\n{warn_text}")


# --- Clear warnings ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clearwarnings(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Please mention a user. Usage: `!clearwarnings @user`")
        return
    clear_warnings(member.id)
    await ctx.send(embed=mod_embed("Clear Warnings", ctx.author, member, color=discord.Color.green()))
    mod_log = discord.utils.get(ctx.guild.text_channels, name="mod-log")
    if mod_log:
        await mod_log.send(embed=mod_embed("Clear Warnings", ctx.author, member, color=discord.Color.green()))


# --- Error handling ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`")
    else:
        await ctx.send(f"An error occurred: {error}")


init_db()
bot.run(TOKEN)
