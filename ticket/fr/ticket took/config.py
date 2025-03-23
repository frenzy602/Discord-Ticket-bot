#--------Ticket-Bot Config File--------#
# Created by WebTheDev #

# Main Config:
botStatusType = 'Watching'  # Bot Status Type (Ex. Playing, Watching, Listening, or Streaming)
botStatusMessage = 'hello'  # The message that is shown on the bot's activity
guildID = 1337639529653469215  # ID of the Guild the bot is running in
ticketLogsChannelID = 1337639529653469218  # ID of the Channel to send system logs to
ticketTranscriptChannelID = 1337648479240978482  # ID of the Channel to send ticket transcripts to
databaseName = 'tickets.db'  # Leave set to default value unless if you want to use a different database name
debugLogSendID = 1071842699759595590  # ID of the Bot Owner to send debug information to

# Ticket Creation/Options Config:
IDOfChannelToSendTicketCreationEmbed = 000000000000000  # ID of the Channel to send the Create a ticket embed to
IDofMessageForTicketCreation = 00000000000000000  # This is auto-adjusted, leave set to 00000000000000000
activeTicketsCategoryID = 000000000000000000000  # ID of the active tickets category
onHoldTicketsCategoryID = 00000000000000  # ID of the onhold tickets category
archivedTicketsCategoryID = 000000000000000000000  # ID of the archived tickets category

OptionsDict = {
    "Option 1": ("🛒 Purchase", "purchase", "For purchasing and order-related inquiries"),
    "Option 2": ("🔧 Support", "support", "For any help or technical support"),
    "Option 3": ("❓ Product Issue", "product", "For any product-related problems")
}

channelPerms = {
    "sales": (000000000000000000000),
    "support": (1337641707755278440, 000000000000000000000),
    "staff": (1337641642873720912, 000000000000000000000)
}

ticketTypeAllowedToCreatePrivateChannels = "staff"  # Set this to be the type of option (roles) as defined in the ticket channel perms dictionary that can use the /create command.
multipleTicketsAllowed = False  # Set this to True if you would like members to be able to have multiple tickets open at once (otherwise set to False).
dmTicketCopies = True  # Set this to True if you would like the bot to dm Ticket Creators transcript copies of their ticket.

# Embed Config:
footerOfEmbeds = ''  # Set a custom embed footer of all embedded messages here!
embedColor = 9d00ff  # Set a custom hex color code for all embeds! Make sure to keep the 0x!

firstRun = True  # This is auto-adjusted, leave set to True on first bot start (unless if you are upgrading to a newer version of the bot, then set to False)