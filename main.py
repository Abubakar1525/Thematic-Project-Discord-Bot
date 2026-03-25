import discord
from discord.ext import commands
from database import init_db, add_warning, get_warnings, clear_warnings
import asyncio
from datetime import timedelta

# Bot configuration
TOKEN = "MTQ4NTI4ODYwNjI4ODU4MDY0OA.GO0zCK.pRwM5sCha73b341dkT4r7raZl2J95NK0KVxu8A"
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


# --- Ping ---
@bot.command()
async def ping(ctx):
    await ctx.send("pong")



# --- Kick ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"Kicked {member.mention} | Reason: {reason}")


# --- Ban ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member.mention} | Reason: {reason}")


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
    await ctx.send(f"Timed out {member.mention} for {minutes} minute(s) | Reason: {reason}")


# --- Remove timeout ---
@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"Removed timeout from {member.mention}")


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
    msg = await ctx.send(f"Deleted {len(deleted) - 1} messages.")
    await asyncio.sleep(3)
    await msg.delete()


# --- Warn ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    add_warning(member.id, ctx.author.id, reason)
    rows = get_warnings(member.id)
    count = len(rows)
    await ctx.send(f"Warned {member.mention} (Warning #{count}) | Reason: {reason}")
    mod_log = discord.utils.get(ctx.guild.text_channels, name="mod-log")
    if mod_log:
        await mod_log.send(
            f"[MOD ACTION]\n"
            f"Moderator: {ctx.author}\n"
            f"User: {member}\n"
            f"Action: Warn\n"
            f"Reason: {reason}"
        )


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
    await ctx.send(f"Warnings cleared for {member.display_name}.")
    mod_log = discord.utils.get(ctx.guild.text_channels, name="mod-log")
    if mod_log:
        await mod_log.send(
            f"[MOD ACTION]\n"
            f"Moderator: {ctx.author}\n"
            f"User: {member}\n"
            f"Action: Clear Warnings"
        )


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
