import discord
import dotenv
import os
import numpy.random as random

bot = discord.Bot() # Create a bot object

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command() # Create a slash command
async def buttons(ctx):
    mangaTitles = ['Button 1', 'Button 2', 'Button 3', 'Button 4']
    correctManga = mangaTitles[0]
    random.shuffle(mangaTitles)

    lostPlayers = set()
    isWinner = []

    class MyView(discord.ui.View):

        async def changeButtonColors(self, state):
            for child in self.children:
                child.disabled = True
                if child.label != correctManga:
                    child.style = discord.ButtonStyle.secondary
                elif state == 'win':
                    child.style = discord.ButtonStyle.success
                elif state == 'loss':
                    child.style = discord.ButtonStyle.danger
            await self.message.edit(view=self)

        async def gameWin(self, interaction):
            if isWinner != []:
                await interaction.response.defer()
            else:
                isWinner.append(interaction.user)
                await ctx.respond(f'{interaction.user} has won!')

        async def buttonPressResponse(self, button, interaction):
            # correct choice -- game ends
            if button.label == correctManga:
                await self.changeButtonColors('win')
                await self.gameWin(interaction)
            # incorrect choice
            else:
                lostPlayers.add(interaction.user)
                await interaction.response.send_message("Sorry, that is the wrong answer!", ephemeral=True)

        async def on_timeout(self):
            if isWinner != []:
                return
            await self.changeButtonColors('loss')
            await ctx.respond(f'No one got the correct answer! The correct answer was {correctManga}.')

        async def repeatedButtonPress(self, interaction):
            try:
                await interaction.response.defer()
            except discord.errors.InteractionResponded:
                pass

        @discord.ui.button(label=mangaTitles[0], row=0, style=discord.ButtonStyle.primary)
        async def first_button_callback(self, button, interaction):
            if interaction.user in lostPlayers:
                await self.repeatedButtonPress(interaction)
            else:
                await self.buttonPressResponse(button, interaction)
                await self.repeatedButtonPress(interaction)

        @discord.ui.button(label=mangaTitles[1], row=1, style=discord.ButtonStyle.primary)
        async def second_button_callback(self, button, interaction):
            if interaction.user in lostPlayers:
                await self.repeatedButtonPress(interaction)
            else:
                await self.buttonPressResponse(button, interaction)
                await self.repeatedButtonPress(interaction)

        @discord.ui.button(label=mangaTitles[2], row=2, style=discord.ButtonStyle.primary)
        async def third_button_callback(self, button, interaction):
            if interaction.user in lostPlayers:
                await self.repeatedButtonPress(interaction)
            else:
                await self.buttonPressResponse(button, interaction)
                await self.repeatedButtonPress(interaction)

        @discord.ui.button(label=mangaTitles[3], row=3, style=discord.ButtonStyle.primary)
        async def fourth_button_callback(self, button, interaction):
            if interaction.user in lostPlayers:
                await self.repeatedButtonPress(interaction)
            else:   
                await self.buttonPressResponse(button, interaction)
                await self.repeatedButtonPress(interaction)
        
    await ctx.respond(view=MyView(timeout=15))

dotenv.load_dotenv()
token = str(os.getenv("TOKEN"))
bot.run(token)