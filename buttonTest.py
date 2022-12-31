import discord
import dotenv
import os

bot = discord.Bot() # Create a bot object

class MyView(discord.ui.View):

    async def bruh():
        print('bruh')

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="You took too long! Disabled all the components.", view=self)

    @discord.ui.button(label="Button 1", row=0, style=discord.ButtonStyle.primary)
    async def first_button_callback(self, button, interaction):
        await bruh()

    @discord.ui.button(label="Button 2", row=1, style=discord.ButtonStyle.primary)
    async def second_button_callback(self, button, interaction):
        await interaction.response.send_message("You pressed me!")

@bot.slash_command() # Create a slash command
async def button(ctx):
    await ctx.respond("This is a button!", view=MyView(timeout=5)) # Send a message with our View class that contains the button

dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
bot.run(token)