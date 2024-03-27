import discord

mainColor = discord.Color.yellow()


def voice_channel_update(mention, voice_channel_name, timestamp, status, action):
    embed = discord.Embed(
        title=f"{status}",
        description=f"{mention} has {action} {voice_channel_name}",
        color=mainColor
    )
    embed.add_field(name="Timestamp", value=timestamp.strftime("%d.%m.%y %H:%M"), inline=False)
    return embed


def working_hours(mention, worked_hours, time_difference, expected_hours, gap_sign):
    embed = discord.Embed(
        title=f"Working Hours",
        description=f"{mention} has worked for {worked_hours} today",
        color=mainColor
    )
    if gap_sign == "-":
        embed.add_field(name="Missing Time", value=time_difference, inline=True)
    elif gap_sign == "+":
        embed.add_field(name="Over Time", value=time_difference, inline=True)
    embed.add_field(name="Required Time", value=expected_hours, inline=True)
    return embed
