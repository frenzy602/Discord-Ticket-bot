import discord
from discord.ext import commands
from discord.ui import View, Select, Button, Modal
import io
import asyncio
from functools import lru_cache
from datetime import datetime
import pytz  # Make sure to install pytz if you haven't already

# Hardcoded bot token (replace with your actual token)
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual bot token

# Dictionary to store ticket categories
OptionsDict = {
    "Option 1": ("Purchase <:cartt:1338268818161668317>", "purchase", "For purchasing and order-related inquiries"),
    "Option 2": ("Support  - <:tic:1338268815863054446>", "support", "For any help or technical support"),
    "Option 3": ("Product Issue <a:su:1338268828244639755>", "product", "For any product-related problems")
}

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TICKET_CATEGORY_NAME = "Tickets"
TRANSCRIPT_CHANNEL_NAME = "ticket-transcripts"
TICKET_PANEL_CHANNEL_ID = 1337644247662202910  # Replace with the ID of the channel where the ticket panel is posted
OWNER_ROLE_ID = 1337641707755278440  # Replace with your Owner Role ID
SUPPORT_ROLE_ID = 1337641642873720912  # Replace with your Support Role ID

# Helper function to fetch category by name
@lru_cache(maxsize=32)
def get_ticket_category(guild):
    return discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)

# Helper function to fetch ticket panel channel
@lru_cache(maxsize=32)
def get_ticket_panel_channel(guild):
    return guild.get_channel(TICKET_PANEL_CHANNEL_ID)

# Validate user input
def validate_input(input_text, max_length=1000):
    if not input_text or len(input_text) > max_length:
        return False
    return True

@bot.event
async def on_ready():
    # Register persistent views
    bot.add_view(TicketPanel())
    bot.add_view(TicketCloseView())
    bot.add_view(TicketControlView())
    print(f"{bot.user} is now online!")

class PurchaseFormModal(discord.ui.Modal, title="Purchase Form"):
    def __init__(self):
        super().__init__()

        # Field for "Do You Agree With Our ToS?"
        self.tos_agreement = discord.ui.TextInput(
            label="Do You Agree With Our ToS?",
            style=discord.TextStyle.short,
            placeholder="Yes/No",
            required=True,
            max_length=3
        )
        self.add_item(self.tos_agreement)

        # Field for "What Product Are You Purchasing?"
        self.product = discord.ui.TextInput(
            label="What Product Are You Purchasing?",
            style=discord.TextStyle.short,
            placeholder="e.g., Nitro, Spotify Boosts",
            required=True,
            max_length=100
        )
        self.add_item(self.product)

        # Field for "Quantity Of The Product"
        self.quantity = discord.ui.TextInput(
            label="Quantity Of The Product",
            style=discord.TextStyle.short,
            placeholder="e.g., 1, 2, 3",
            required=True,
            max_length=10
        )
        self.add_item(self.quantity)

        # Field for "Payment Mode?"
        self.payment_method = discord.ui.TextInput(
            label="Payment Mode?",
            style=discord.TextStyle.short,
            placeholder="e.g., UPI, LTC, PayPal, Cashapp",
            required=True,
            max_length=50
        )
        self.add_item(self.payment_method)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ticket_category = get_ticket_category(guild)

        if not ticket_category:
            await interaction.response.send_message(f"Category `{TICKET_CATEGORY_NAME}` not found. Please create it.", ephemeral=True)
            return

        # Check if the user already has an open ticket
        for channel in guild.text_channels:
            if channel.topic and f":User               {interaction.user.id}" in channel.topic:
                await interaction.response.send_message(f"You already have an open ticket: {channel.mention}", ephemeral=True)
                return

        channel_name = f"purchase-{interaction.user.name}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for role_id in [OWNER_ROLE_ID, SUPPORT_ROLE_ID]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_panel_channel = get_ticket_panel_channel(guild)
        if not ticket_panel_channel:
            await interaction.response.send_message("Ticket panel channel not found. Please set the correct ID.", ephemeral=True)
            return

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=ticket_category,
            overwrites=overwrites,
            position=ticket_panel_channel.position + 1,
            topic=f":User               {interaction.user.id}"
        )

        # Send a separate message with the purchase details
        initial_embed = discord.Embed(
            title="Purchase Ticket Details",
            description=f"<:dd:1338269535748358144> Thank you {interaction.user.mention} for your purchase inquiry!\n\n"
                        f"<:dd:1338269535748358144> Our staff is currently reviewing your request and working diligently to provide you with the best assistance.",
            color=int('9d00ff', 16)  # Dark purple color
        )
        initial_embed.set_footer(text="Thank you for your patience")
        initial_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await ticket_channel.send(embed=initial_embed, view=TicketCloseView())

        # Tag the support role
        support_role = guild.get_role(SUPPORT_ROLE_ID)
        if support_role:
            await ticket_channel.send(f"{support_role.mention}.")

        # Second message: Purchase details in an embed with dark purple color
        purchase_details_embed = discord.Embed(
            title="Purchase Details",
            color=int('9d00ff', 16)  # Dark purple color
        )
        purchase_details_embed.add_field(name="Do you agree with our TOS?", value=f"```{self.tos_agreement.value}```", inline=False)
        purchase_details_embed.add_field(name="What product are you purchasing?", value=f"```{self.product.value}```", inline=False)
        purchase_details_embed.add_field(name="Quantity of the product", value=f"```{self.quantity.value}```", inline=False)
        purchase_details_embed.add_field(name="Payment Mode?", value=f"```{self.payment_method.value}```", inline=False)

        await ticket_channel.send(embed=purchase_details_embed)

        # Notify the user that the ticket has been created with an embed
        ticket_created_embed = discord.Embed(
            title="Ticket Created",
            description=f"Your ticket has been created in {ticket_channel.mention}",
            color=discord.Color.green()
        )
        ticket_created_embed.set_footer(text="Only you can see this - Dismiss message")
        ticket_created_embed.timestamp = datetime.now(pytz.timezone('Asia/Kolkata'))

        await interaction.response.send_message(embed=ticket_created_embed, ephemeral=True)

class SupportFormModal(discord.ui.Modal, title="Support Form"):
    def __init__(self):
        super().__init__()

        # Field for "What do you need help with?"
        self.help_description = discord.ui.TextInput(
            label="What do you need help with?",
            style=discord.TextStyle.short,
            placeholder="Describe what you need help with...",
            required=True,
            max_length=99
        )
        self.add_item(self.help_description)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ticket_category = get_ticket_category(guild)

        if not ticket_category:
            await interaction.response.send_message(f"Category `{TICKET_CATEGORY_NAME}` not found. Please create it.", ephemeral=True)
            return

        # Check if the user already has an open ticket
        for channel in guild.text_channels:
            if channel.topic and f":User               {interaction.user.id}" in channel.topic:
                await interaction.response.send_message(f"You already have an open ticket: {channel.mention}", ephemeral=True)
                return

        channel_name = f"support-{interaction.user.name}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for role_id in [OWNER_ROLE_ID, SUPPORT_ROLE_ID]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_panel_channel = get_ticket_panel_channel(guild)
        if not ticket_panel_channel:
            await interaction.response.send_message("Ticket panel channel not found. Please set the correct ID.", ephemeral=True)
            return

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=ticket_category,
            overwrites=overwrites,
            position=ticket_panel_channel.position + 1,
            topic=f":User               {interaction.user.id}"
        )

        # Send a separate message with the support details
        initial_embed = discord.Embed(
            title="Support Ticket Details",
            description=f"<:dd:1338269535748358144> Thank you {interaction.user.mention} for your support inquiry!\n\n"
                        f"<:dd:1338269535748358144> Our staff is currently reviewing your request and working diligently to provide you with the best assistance.",
            color=int('9d00ff', 16)  # Dark purple color
        )
        initial_embed.set_footer(text="Thank you for your patience")
        initial_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await ticket_channel.send(embed=initial_embed, view=TicketCloseView())

        # Tag the support role
        support_role = guild.get_role(SUPPORT_ROLE_ID)
        if support_role:
            await ticket_channel.send(f"{support_role.mention} A new support ticket has been created by {interaction.user.mention}.")

        # Second message: Support details in an embed with dark purple color
        support_details_embed = discord.Embed(
            title="Support Details",
            color=int('9d00ff', 16)  # Dark purple color
        )
        support_details_embed.add_field(name="What do you need help with?", value=f"**{self.help_description.value}**", inline=False)

        await ticket_channel.send(embed=support_details_embed)

        # Notify the user that the ticket has been created with an embed
        ticket_created_embed = discord.Embed(
            title="Ticket Created",
            description=f"Your ticket has been created in {ticket_channel.mention}",
            color=discord.Color.green()
        )
        ticket_created_embed.set_footer(text="Only you can see this - Dismiss message")
        ticket_created_embed.timestamp = datetime.now(pytz.timezone('Asia/Kolkata'))

        await interaction.response.send_message(embed=ticket_created_embed, ephemeral=True)

class ProductIssueFormModal(discord.ui.Modal, title="Product Issue Form"):
    def __init__(self):
        super().__init__()

        # Field for "What do you need help with?"
        self.issue_description = discord.ui.TextInput(
            label="What do you need help with?",
            style=discord.TextStyle.short,
            placeholder="Nitro/Netflix/Spotify",
            required=True,
            max_length=99
        )
        self.add_item(self.issue_description)

        # Field for "Buying date"
        self.buying_date = discord.ui.TextInput(
            label="Buying date",
            style=discord.TextStyle.short,
            placeholder="22 Dec 2024",
            required=True,
            max_length=99
        )
        self.add_item(self.buying_date)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ticket_category = get_ticket_category(guild)

        if not ticket_category:
            await interaction.response.send_message(f"Category `{TICKET_CATEGORY_NAME}` not found. Please create it.", ephemeral=True)
            return

        # Check if the user already has an open ticket
        for channel in guild.text_channels:
            if channel.topic and f":User               {interaction.user.id}" in channel.topic:
                await interaction.response.send_message(f"You already have an open ticket: {channel.mention}", ephemeral=True)
                return

        channel_name = f"product-issue-{interaction.user.name}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for role_id in [OWNER_ROLE_ID, SUPPORT_ROLE_ID]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_panel_channel = get_ticket_panel_channel(guild)
        if not ticket_panel_channel:
            await interaction.response.send_message("Ticket panel channel not found. Please set the correct ID.", ephemeral=True)
            return

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=ticket_category,
            overwrites=overwrites,
            position=ticket_panel_channel.position + 1,
            topic=f":User               {interaction.user.id}"
        )

        # Send a separate message with the product issue details
        initial_embed = discord.Embed(
            title="Product Issue Ticket Details",
            description=f"<:dd:1338269535748358144> Thank you {interaction.user.mention} for your product issue inquiry!\n\n"
                        f"<:dd:1338269535748358144> Our staff is currently reviewing your request and working diligently to provide you with the best assistance.",
            color=int('9d00ff', 16)  # Dark purple color
        )
        initial_embed.set_footer(text="Thank you for your patience")
        initial_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await ticket_channel.send(embed=initial_embed, view=TicketCloseView())

        # Tag the support role
        support_role = guild.get_role(SUPPORT_ROLE_ID)
        if support_role:
            await ticket_channel.send(f"{support_role.mention} A new product issue ticket has been created by {interaction.user.mention}.")

        # Second message: Product issue details in an embed with dark purple color
        product_issue_details_embed = discord.Embed(
            title="Product Issue Details",
            color=int('9d00ff', 16)  # Dark purple color
        )
        product_issue_details_embed.add_field(name="What do you need help with?", value=f"**{self.issue_description.value}**", inline=False)
        product_issue_details_embed.add_field(name="Buying date", value=f"**{self.buying_date.value}**", inline=False)

        await ticket_channel.send(embed=product_issue_details_embed)

        # Notify the user that the ticket has been created with an embed
        ticket_created_embed = discord.Embed(
            title="Ticket Created",
            description=f"Your ticket has been created in {ticket_channel.mention}",
            color=discord.Color.green()
        )
        ticket_created_embed.set_footer(text="Only you can see this - Dismiss message")
        ticket_created_embed.timestamp = datetime.now(pytz.timezone('Asia/Kolkata'))

        await interaction.response.send_message(embed=ticket_created_embed, ephemeral=True)

class TicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Purchase", description="For purchasing and order-related inquiries", emoji="<:cartt:1338268818161668317>"),
            discord.SelectOption(label="Support", description="For any help or technical support", emoji="<:tic:1338268815863054446>"),
            discord.SelectOption(label="Product Issue", description="For any product-related problems", emoji="<a:su:1338268828244639755>"),
        ]
        super().__init__(placeholder="Select a category...", options=options, custom_id="ticket_dropdown")

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]  # Get the selected option
        print(f"Selected option: {selected_option}")  # Debugging

        if selected_option == "Purchase":
            print("Purchase option selected")  # Debugging
            await interaction.response.send_modal(PurchaseFormModal())
        elif selected_option == "Support":
            print("Support option selected")  # Debugging
            await interaction.response.send_modal(SupportFormModal())
        elif selected_option == "Product Issue":
            print("Product Issue option selected")  # Debugging
            await interaction.response.send_modal(ProductIssueFormModal())

        # Reset the dropdown after selection
        await interaction.message.edit(view=TicketPanel())

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="close_ticket_button")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel
        guild = interaction.guild

        # Save transcript
        transcript_category = discord.utils.get(guild.categories, name="ticket-transcripts")
        if not transcript_category:
            transcript_category = await guild.create_category("ticket-transcripts")

        transcript_channel = discord.utils.get(transcript_category.channels, name=TRANSCRIPT_CHANNEL_NAME)
        if not transcript_channel:
            transcript_channel = await transcript_category.create_text_channel(TRANSCRIPT_CHANNEL_NAME)

        messages = [msg async for msg in channel.history(limit=None)]
        transcript_lines = [
            f"[{msg.created_at}] {msg.author}: {msg.content}" for msg in messages
        ]
        transcript = "\n".join(transcript_lines)

        if not transcript:
            await interaction.followup.send("No messages found in this ticket.", ephemeral=True)
            return

        transcript_file = io.StringIO(transcript)
        transcript_file.seek(0)
        transcript_file = discord.File(fp=transcript_file, filename=f"transcript-{channel.name}.txt")

        channel_topic = channel.topic
        opener_username = "Unknown"
        if channel_topic and ':User               ' in channel_topic:
            user_id = channel_topic.split(':User               ')[-1].strip()
            try:
                ticket_opener = await bot.fetch_user(int(user_id))
                opener_username = ticket_opener.name
            except (ValueError, IndexError):
                print(f"Could not parse user ID from topic: {channel_topic}")

        closer_username = interaction.user.name

        ist_timezone = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist_timezone).strftime("%Y-%m-%d %H:%M:%S")

        embed = discord.Embed(
            title=f"Transcript for {channel.name}",
            description=f"**Ticket Closed By:** {closer_username}\n"
                        f"**Ticket Opener:** {opener_username}\n"
                        f"**Date and Time (IST):** {current_time_ist}",
            color=discord.Color.green()
        )

        await transcript_channel.send(embed=embed, file=transcript_file)

        try:
            if ticket_opener and not ticket_opener.bot:
                dm_embed = discord.Embed(
                    title="Ticket Closed",
                    description=f"Your ticket has been closed in **{guild.name}**.",
                    color=discord.Color.blue()
                )
                dm_embed.add_field(name="Ticket Information", value=f"Category: {channel.name.split('-')[0]}\nClaimed by: Not claimed\nTotal Messages: {len(messages)}", inline=False)
                dm_embed.add_field(name="Transcript", value=f"**Ticket Closed By:** {closer_username}\n"
                                                            f"**Ticket Opener:** {opener_username}\n"
                                                            f"**Date and Time (IST):** {current_time_ist}", inline=False)

                await ticket_opener.send(
                    content=f"Your ticket transcript from {guild.name}:",
                    embed=dm_embed,
                    file=discord.File(fp=io.StringIO(transcript), filename=f"transcript-{channel.name}.txt")
                )
        except discord.Forbidden:
            print(f"Could not DM user {ticket_opener.id} - DMs disabled")
        except Exception as e:
            print(f"Error sending DM: {e}")

        # Remove the user from the ticket channel
        if ticket_opener:
            await channel.set_permissions(ticket_opener, read_messages=False, send_messages=False)

        # Send a message with buttons for transcript, open, and delete
        control_embed = discord.Embed(
            title="Ticket Closed",
            description=f"Ticket closed by {closer_username}.\n\nUse the buttons below to manage the ticket.",
            color=discord.Color.orange()
        )
        control_view = TicketControlView()
        await channel.send(embed=control_embed, view=control_view)

        # Send a separate message with the ticket closed information
        ticket_closed_message = await channel.send(f"Ticket closed by {interaction.user.mention}")
        await ticket_closed_message.add_reaction("📝")  # Transcript
        await ticket_closed_message.add_reaction("🔓")  # Open
        await ticket_closed_message.add_reaction("⛔")  # Delete

        await interaction.followup.send("Ticket has been closed. User removed from the ticket.", ephemeral=True)

        class TicketControlView(View):
            def __init__(self):
                super().__init__(timeout=None)

                # Add buttons in a single row with unique custom_id values
                self.add_item(Button(style=discord.ButtonStyle.secondary, label="Transcript", emoji="📝", custom_id="view_transcript_button"))
                self.add_item(Button(style=discord.ButtonStyle.secondary, label="Open", emoji="🔓", custom_id="reopen_ticket_button"))
                self.add_item(Button(style=discord.ButtonStyle.secondary, label="Delete", emoji="⛔", custom_id="delete_ticket_button"))

            @discord.ui.button(label="Transcript", style=discord.ButtonStyle.secondary, emoji="📝", custom_id="view_transcript_button")
            async def view_transcript(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                # Logic to send the transcript to the user
                await interaction.followup.send("Transcript sent to your DMs.", ephemeral=True)

            @discord.ui.button(label="Open", style=discord.ButtonStyle.secondary, emoji="🔓", custom_id="reopen_ticket_button")
            async def reopen_ticket(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                channel = interaction.channel
                guild = interaction.guild

                ticket_category = get_ticket_category(guild)
                if not ticket_category:
                    await interaction.followup.send("Ticket category not found. Please create it.", ephemeral=True)
                    return

                await channel.edit(category=ticket_category, sync_permissions=True)
                await interaction.followup.send("Ticket has been reopened.", ephemeral=True)

            @discord.ui.button(label="Delete", style=discord.ButtonStyle.secondary, emoji="⛔", custom_id="delete_ticket_button")
            async def delete_ticket(self, interaction: discord.Interaction, button: Button):
                await interaction.response.defer(ephemeral=True)
                channel = interaction.channel

                countdown_msg = await channel.send("This ticket will be deleted in 5 seconds...")
                for i in range(5, 0, -1):
                    await asyncio.sleep(1)
                    await countdown_msg.edit(content=f"This ticket will be deleted in {i} seconds...")

                await channel.delete()

@bot.command()
async def setup(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You need administrator permissions to use this command.")
        return

    embed = discord.Embed(
        title="Frenzy Tickets",
        description="<:d_:1338268820317536356> <:cartt:1338268818161668317> **Purchase** - For purchasing and order-related inquiries.\n<:d_:1338268820317536356><:tic:1338268815863054446> **Support** - For any help or technical support\n<:d_:1338268820317536356> <a:su:1338268828244639755> **Product Issue** - For any product-related problems.",
        color=int('9d00ff', 16)
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/971334710221471744/1338259978661793814/frenzy_btp.png?ex=67aa6f3a&is=67a91dba&hm=504dbbfdc40de1e2ac9c09dec89c9bf043af3fcd1b4929538faf4afd404aa3a2&")

    await ctx.send(embed=embed, view=TicketPanel())

# Run the bot with the hardcoded token
bot.run(BOT_TOKEN)
