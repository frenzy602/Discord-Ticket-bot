import discord
from discord.ext import commands

# Enable all intents (adjust based on what you actually need)
intents = discord.Intents.all()

# Initialize the bot with a prefix and intents
bot = commands.Bot(command_prefix=commands.when_mentioned_or('-'), intents=intents)

# Example of an event
@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

# Example of a command
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Run the bot (add your token here or use environment variables)
if __name__ == "__main__":
    bot.run("MTMzNzMyOTE1NjQxNjg2ODQxNA.G5J9rT.TQehJDVT0kW6vMfOHY8x4EVKIuhMSut58-wYL8")
