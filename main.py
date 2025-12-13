import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio

# ------------------------
# CONFIG
# ------------------------

BOT_OWNER_ID = 1205887699609853972  # <-- PUT YOUR DISCORD ID HERE

# ------------------------
# Bot Setup
# ------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("TOKEN")

server_ticket_categories = {}

# ------------------------
# Ticket Views
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
# Slash Commands
# ------------------------

@bot.tree.command(description="Send the ticket panel")
async def ticketpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description="Click below to create a ticket.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(description="Set the ticket category")
@app_commands.describe(category="Ticket category")
async def setcategory(interaction: discord.Interaction, category: discord.CategoryChannel):
    server_ticket_categories[interaction.guild.id] = category.id
    await interaction.response.send_message(
        f"✅ Ticket category set to **{category.name}**",
        ephemeral=True
    )

# ------------------------
# ANNOUNCEMENT COMMAND (OWNER ONLY)
# ------------------------

@bot.tree.command(description="Send a DM announcement to all users (owner only)")
@app_commands.describe(message="Announcement message")
async def announceall(interaction: discord.Interaction, message: str):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message(
            "❌ You are not allowed to use this command.",
            ephemeral=True
        )
        return

    await interaction.response.send_message("📤 Sending announcement...", ephemeral=True)

    sent = 0
    failed = 0

    for guild in bot.guilds:
        for member in guild.members:
            if member.bot:
                continue
            try:
                await member.send(
                    embed=discord.Embed(
                        title="📢 Announcement",
                        description=message,
                        color=discord.Color.blue()
                    )
                )
                sent += 1
            except:
                failed += 1

    await interaction.followup.send(
        f"✅ Sent to {sent} users\n❌ Failed: {failed}",
        ephemeral=True
    )

# ------------------------
# Bot Ready
# ------------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name="APT"
    )

    await bot.change_presence(status=discord.Status.online, activity=activity)

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Sync failed:", e)

# ------------------------
# Start Bot
# ------------------------

bot.run(TOKEN)
