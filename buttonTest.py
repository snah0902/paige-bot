import discord
import dotenv
import os

bot = discord.Bot() # Create a bot object

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

class MyView(discord.ui.View):

    async def answerResponse(self, button):
        for child in self.children:
            child.disabled = True
            if child != button:
                child.style = discord.ButtonStyle.secondary
            else:
                if child.label == 'Button 1':
                    child.style = discord.ButtonStyle.success
                else:
                    child.style = discord.ButtonStyle.danger
        await self.message.edit(view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)

    @discord.ui.button(label="Button 1", row=0, style=discord.ButtonStyle.primary)
    async def first_button_callback(self, button, interaction):
        await interaction.response.send_message("Correct!")
        await self.answerResponse(button)

    @discord.ui.button(label="Button 2", row=1, style=discord.ButtonStyle.primary)
    async def second_button_callback(self, button, interaction):
        await interaction.response.send_message("Incorrect!")
        await self.answerResponse(button)

@bot.slash_command() # Create a slash command
async def button(ctx):
    await ctx.respond("This is a button!", view=MyView(timeout=15)) # Send a message with our View class that contains the button

dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
bot.run(token)