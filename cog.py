import asyncio
import logging
import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from tortoise.exceptions import DoesNotExist

from ballsdex.core.models import Ball, BallInstance, Player, balls

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("ballsdex.packages.wheel")


@app_commands.guild_only()
class Wheel(commands.GroupCog):
    """
    Rueda de la suerte
    """
    
    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    def get_wheel_probability(self, rarity: float) -> float:
        """
        calculate the probability
        """
        if 200 >= rarity >= 180:
            return 0.80
        elif 160 >= rarity >= 120:
            return 0.60
        elif 100 >= rarity >= 80:
            return 0.50
        elif 70 >= rarity >= 50:
            return 0.30
        elif 20 >= rarity >= 10:
            return 0.15
        elif 7 >= rarity >= 1:
            return 0.01
        else:
            return 0.05

    def select_ball_by_rarity(self) -> Ball:
        """
        select a ball
        """
        enabled_balls = [ball for ball in balls.values() if ball.enabled and ball.rarity > 0]
        
        if not enabled_balls:
            raise ValueError("no balls found")
        
        weights = []
        for ball in enabled_balls:
            probability = self.get_wheel_probability(ball.rarity)
            weights.append(probability)
        
        total_weight = sum(weights)
        if total_weight == 0:
            weights = [1.0] * len(enabled_balls)
        else:
            weights = [w / total_weight for w in weights]
        
        selected_ball = random.choices(enabled_balls, weights=weights)[0]
        return selected_ball

    def get_wheel_probability(self, rarity: float) -> float:
        """
        calculate the probability of get a ball
        """
        if 200 >= rarity >= 180:
            return 0.80
        elif 160 >= rarity >= 120:
            return 0.60
        elif 100 >= rarity >= 80:
            return 0.50
        elif 70 >= rarity >= 50:
            return 0.30
        elif 20 >= rarity >= 10:
            return 0.15
        elif 7 >= rarity >= 1:
            return 0.01
        else:
            return 0.05

    async def create_ball_instance(self, player: Player, ball: Ball) -> BallInstance:
        """
        create a new ball
        """
        attack_bonus = random.randint(-20, 20)
        health_bonus = random.randint(-20, 20)
        
        ball_instance = await BallInstance.create(
            ball=ball,
            player=player,
            server_id=None,
            attack_bonus=attack_bonus,
            health_bonus=health_bonus,
        )
        return ball_instance

    @app_commands.command(name="about", description="Muestra información sobre la ruleta.")
    async def about(self, interaction: discord.Interaction):
        """
        Muestra información sobre la ruleta.
        """
        embed = discord.Embed(
            title="🎡 Ruleta de la Suerte 🎡",
            description=(
                "Esta es una ruleta en la que podrías conseguir diferentes balls girandola!\n\n"
                "Debes de usar el comando `/wheel spin` para girar la ruleta!\n\n"
                "**Rareza de conseguir cada ball:**\n"
                "• Rareza 200-180: 80%\n"
                "• Rareza 160-120: 60%\n"
                "• Rareza 100-80: 50%\n"
                "• Rareza 70-50: 30%\n"
                "• Rareza 20-10: 15%\n"
                "• Rareza 7-1: 1%\n\n"
                "La ruleta se puede girar cada 8 horas."
            ),
            color=discord.Color.green()
        )
        
        embed.set_image(url="https://media.discordapp.net/attachments/1463913792537890906/1465375111610634260/HiPaint_1769443017797.png")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="spin", description="Gira la ruleta para obtener una ball")
    @app_commands.checks.cooldown(1, 28800, key=lambda i: i.user.id)
    async def spin(self, interaction: discord.Interaction):
        """
        Gira la ruleta para obtener una ball.
        """
        await interaction.response.defer()
        
        try:
            player = await Player.get(discord_id=interaction.user.id)
        except DoesNotExist:
            await interaction.followup.send(
                "esto es un error xd. no se q poner aqui ya que no deberia pasar",
                ephemeral=True
            )
            return
        
        spinning_embed = discord.Embed(
            title="🎡 La ruleta se está girando... 🎡",
            description="Esto podría tomar un poco de tiempo",
            color=discord.Color.blue()
        )
        
        spinning_message = await interaction.followup.send(embed=spinning_embed)
        
        await asyncio.sleep(3)
        
        try:
            selected_ball = self.select_ball_by_rarity()
            
            ball_instance = await self.create_ball_instance(player, selected_ball)
            
            ball_emoji = ""
            try:
                emoji = self.bot.get_emoji(selected_ball.emoji_id)
                if emoji:
                    ball_emoji = str(emoji)
            except (ValueError, AttributeError):
                pass
            
            result_embed = discord.Embed(
                title="🎡 La ruleta ha parado, tu premio es... 🎉",
                description=(
                    f"{ball_emoji}**{selected_ball.country}** `(#{ball_instance.pk:0X}, {ball_instance.attack_bonus:+d}%/{ball_instance.health_bonus:+d}%)`\n\n"
                    f"⭐ Rareza: {selected_ball.rarity}"
                ),
                color=discord.Color.green()
            )
            
            result_embed.set_footer(
                text=f"Debes esperar 8 horas para poder volver a girar la ruleta!"
            )
            
            result_embed.set_image(url="https://media.discordapp.net/attachments/1463913792537890906/1465375111610634260/HiPaint_1769443017797.png")
            
            await spinning_message.edit(embed=result_embed)
            
        except Exception as e:
            log.error(f"error al girar la ruleta del usuario grasoso {interaction.user.id}: {e}")
            await interaction.followup.send(
                "Ocurrió un error al girar la ruleta. Contacta soporte.",
                ephemeral=True
            )
