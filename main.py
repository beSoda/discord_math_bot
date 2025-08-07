import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import math
import random
from collections import defaultdict
import time


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log',encoding='utf-8',mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send (f"Welcome to the server {member.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "shit" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} - use another word.")

    await bot.process_commands(message)

@bot.command()
async def commands(ctx):
    await ctx.send(f"!commands - Load commands")
    await ctx.send(f"!poll - Create poll")
    await ctx.send(f"!guess - Pick a number")
    await ctx.send(f"!leaderboard- number game leaderboard")

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")


leaderboard = defaultdict(lambda: {"wins": 0, "total_attempts": 0, "games_played": 0})

@bot.command()
async def guess(ctx):
    difficulty_levels = {
        "easy": {"range": (1, 50), "attempts": 8, "hint_after": 3},
        "medium": {"range": (1, 100), "attempts": 10, "hint_after": 4},
        "hard": {"range": (1, 200), "attempts": 12, "hint_after": 5},
        "extreme": {"range": (1, 999), "attempts": 15, "hint_after": 13},
    }

    embed = discord.Embed(
        title="Guess the Number - Choose Difficulty",
        description=(
            "🎮 **Pick a difficulty level**:\n"
            "- **Easy**: Numbers 1-50, 8 attempts\n"
            "- **Medium**: Numbers 1-100, 10 attempts\n"
            "- **Hard**: Numbers 1-200, 12 attempts\n"
            "- **Extreme**: Numbers 1-999, 15 attempts\n"         
            "Type `easy`, `medium`, `hard`, or `extreme` to start!"
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

    def check_difficulty(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in difficulty_levels

    try:
        difficulty_msg = await ctx.bot.wait_for('message', check=check_difficulty, timeout=15)
        difficulty = difficulty_msg.content.lower()
    except TimeoutError:
        difficulty = "medium"
        await ctx.send(embed=discord.Embed(
            description="⏳ You took too long! Defaulting to **Medium** difficulty.",
            color=discord.Color.orange()
        ))

    level = difficulty_levels[difficulty]
    min_num, max_num = level["range"]
    max_attempts = level["attempts"]
    hint_after = level["hint_after"]
    target_number = random.randint(min_num, max_num)
    attempts = 0
    hints_given = 0
    start_time = time.time()

    embed = discord.Embed(
        title=f"Guess the Number ({difficulty.capitalize()})",
        description=(
            f"🎲 I'm thinking of a number between **{min_num}** and **{max_num}**.\n"
            f"You have **{max_attempts} attempts** to guess it! Let's go!"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    def check_guess(m):
        return m.author == ctx.author and m.channel == ctx.channel

    while attempts < max_attempts:
        try:
            guess_message = await ctx.bot.wait_for('message', check=check_guess, timeout=15)
            guess_str = guess_message.content

            try:
                guess = int(guess_str)
                if guess < min_num or guess > max_num:
                    await ctx.send(embed=discord.Embed(
                        description=f"⚠️ Please guess a number between **{min_num}** and **{max_num}**!",
                        color=discord.Color.red()
                    ))
                    continue
            except ValueError:
                await ctx.send(embed=discord.Embed(
                    description="❌ Invalid input. Please enter a number!",
                    color=discord.Color.red()
                ))
                continue

            attempts += 1

            if guess < target_number:
                await ctx.send(embed=discord.Embed(
                    description=f"⬇️ Too low! **{max_attempts - attempts} attempts** left.",
                    color=discord.Color.yellow()
                ))
            elif guess > target_number:
                await ctx.send(embed=discord.Embed(
                    description=f"⬆️ Too high! **{max_attempts - attempts} attempts** left.",
                    color=discord.Color.yellow()
                ))
            else:
                leaderboard[ctx.author.id]["wins"] += 1
                leaderboard[ctx.author.id]["total_attempts"] += attempts
                leaderboard[ctx.author.id]["games_played"] += 1
                time_taken = round(time.time() - start_time, 2)

                embed = discord.Embed(
                    title="🎉 Victory!",
                    description=(
                        f"You guessed the number **{target_number}** in **{attempts} attempts**!\n"
                        f"Time taken: **{time_taken} seconds**.\n"
                        f"Leaderboard stats: **{leaderboard[ctx.author.id]['wins']} wins**, "
                        f"**{leaderboard[ctx.author.id]['games_played']} games played**."
                    ),
                    color=discord.Color.gold()
                )
                await ctx.send(embed=embed)
                return

            if attempts == hint_after and hints_given == 0:
                hint = "💡 **Hint**: "
                if target_number % 2 == 0:
                    hint += "The number is **even**."
                else:
                    hint += "The number is **odd**."
                if target_number > (min_num + max_num) // 2:
                    hint += f" It's **greater than {(min_num + max_num) // 2}**."
                else:
                    hint += f" It's **less than or equal to {(min_num + max_num) // 2}**."
                await ctx.send(embed=discord.Embed(description=hint, color=discord.Color.purple()))
                hints_given += 1

        except TimeoutError:
            await ctx.send(embed=discord.Embed(
                description="⏳ You took too long to guess! Game over.",
                color=discord.Color.red()
            ))
            return

    leaderboard[ctx.author.id]["games_played"] += 1
    leaderboard[ctx.author.id]["total_attempts"] += attempts

    await ctx.send(embed=discord.Embed(
        title="Game Over",
        description=(
            f"😔 You ran out of attempts! The number was **{target_number}**.\n"
            f"Leaderboard stats: **{leaderboard[ctx.author.id]['wins']} wins**, "
            f"**{leaderboard[ctx.author.id]['games_played']} games played**."
        ),
        color=discord.Color.red()
    ))

@bot.command()
async def leaderboard(ctx):
    # Access the leaderboard data through the bot object
    if not bot.leaderboard_data: # Now 'bot.leaderboard_data' refers to your dictionary
        await ctx.send(embed=discord.Embed(
            description="🏆 No games played yet!",
            color=discord.Color.blue()
        ))
        return

    embed = discord.Embed(title="🏆 Guess the Number Leaderboard", color=discord.Color.blue())
    sorted_leaderboard = sorted(
        bot.leaderboard_data.items(), # And here as well
        key=lambda x: (x[1]["wins"], -x[1]["total_attempts"]),
        reverse=True
    )

    for i, (user_id, stats) in enumerate(sorted_leaderboard[:5], 1):
        try:
            user = await ctx.bot.fetch_user(user_id)
            user_display_name = user.display_name
        except discord.NotFound:
            user_display_name = f"Unknown User (ID: {user_id})"

        avg_attempts = stats["total_attempts"] / stats["games_played"] if stats["games_played"] > 0 else 0
        embed.add_field(
            name=f"{i}. {user_display_name}",
            value=f"Wins: {stats['wins']} | Games: {stats['games_played']} | Avg Attempts: {avg_attempts:.2f}",
            inline=False
        )

    await ctx.send(embed=embed)


bot.run(token, log_handler=handler, log_level=logging.DEBUG)


