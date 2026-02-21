from datetime import datetime
from typing import TYPE_CHECKING

from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from ballsdex.core.models import Player


class WheelSpin(Model):
    """
    Model to track wheel spins for each player
    """
    player_id: int
    
    player: fields.ForeignKeyRelation["Player"] = fields.ForeignKeyField(
        "models.Player", related_name="wheel_spins", on_delete=fields.CASCADE
    )
    last_spin = fields.DatetimeField(
        description="Last time the player spun the wheel", null=True
    )
    daily_spins = fields.IntField(
        description="Number of spins used today", default=0
    )
    spin_date = fields.DateField(
        description="Date for tracking daily spins", auto_now_add=True
    )
    
    class Meta:
        table = "wheel_spin"
        unique_together = ("player", "spin_date")
    
    def __str__(self) -> str:
        return f"WheelSpin for player {self.player_id} - {self.daily_spins}/3 spins"
