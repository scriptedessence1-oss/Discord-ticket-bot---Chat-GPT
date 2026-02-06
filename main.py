import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio

# ------------------------
# CONFIG
# ------------------------

BOT_OWNER_ID = 1205887699609853972
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

TOKEN = os.getenv("DISCORD_TOKEN")

# ------------------------
# BOT SETUP
# ------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

server_ticket_categories = {}
warnings = {}

# ------------------------
# TICKET VIEWS
# ------------------------

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.green)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        if guild.id not in server_ticket_categories:
            await interaction.response.send_message(
                "❌ No ticket category set. Use `/setcategory` first.",
                ephemeral=True
            )
            return

        category = guild.get_channel(server_ticket_categories[guild.id])

        channel = await category.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )

        await channel.send(
            f"🎫 **Ticket opened by {interaction.user.mention}**",
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❌ Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await asyncio.sleep(1)
        await interaction.channel.delete()

# ------------------------
# SLASH COMMANDS
# ------------------------

@bot.tree.command(description="Send the ticket panel")
async def ticketpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description="Click the button below to create a ticket.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(description="Set ticket category")
async def setcategory(interaction: discord.Interaction, category: discord.CategoryChannel):
    server_ticket_categories[interaction.guild.id] = category.id
    await interaction.response.send_message(
        f"✅ Ticket category set to **{category.name}**",
        ephemeral=True
    )

# ------------------------
# MODERATION COMMANDS
# ------------------------

@bot.tree.command(description="Warn a user")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    warnings.setdefault(member.id, []).append(reason)

    try:
        await member.send(f"⚠️ You were warned: {reason}")
    except:
        pass

    await interaction.response.send_message(
        f"⚠️ {member.mention} warned.",
        ephemeral=True
    )

@bot.tree.command(description="Remove a warning")
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    warnings.pop(member.id, None)
    await interaction.response.send_message(
        f"✅ Warnings cleared for {member.mention}",
        ephemeral=True
    )

@bot.tree.command(description="Mute a user")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
    duration = minutes * 60
    await member.timeout(discord.utils.utcnow() + discord.timedelta(seconds=duration))

    try:
        await member.send(f"🔇 You were muted for {minutes} minutes.\nReason: {reason}")
    except:
        pass

    await interaction.response.send_message(
        f"🔇 {member.mention} muted for {minutes} minutes.",
        ephemeral=True
    )

@bot.tree.command(description="Kick a user")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str):
    await member.kick(reason=reason)
    await interaction.response.send_message(
        f"👢 {member} kicked.",
        ephemeral=True
    )

@bot.tree.command(description="Ban a user")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):
    await member.ban(reason=reason)
    await interaction.response.send_message(
        f"🔨 {member} banned.",
        ephemeral=True
    )

@bot.tree.command(description="Lock a channel")
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        send_messages=False
    )
    await interaction.response.send_message("🔒 Channel locked.", ephemeral=True)

@bot.tree.command(description="Unlock a channel")
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        send_messages=True
    )
    await interaction.response.send_message("🔓 Channel unlocked.", ephemeral=True)

# ------------------------
# OWNER ANNOUNCEMENT
# ------------------------

@bot.tree.command(description="Send announcement DM (Owner only)")
async def broadcast(interaction: discord.Interaction, message: str):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        return

    await interaction.response.send_message("📢 Sending announcement...", ephemeral=True)

    sent = 0
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot:
                try:
                    await member.send(message)
                    sent += 1
                except:
                    pass

    await interaction.followup.send(f"✅ Sent to {sent} users.", ephemeral=True)

# ------------------------
# READY EVENT
# ------------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Sync error:", e)

# ------------------------
# START BOT
# ------------------------

bot.run(TOKEN)
