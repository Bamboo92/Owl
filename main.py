from typing import Final
import os
from dotenv import load_dotenv
import asyncio
from discord import Intents, errors, app_commands, Interaction, CustomActivity, Status, Member
from discord.ext import commands
from datetime import timedelta
import embedded
import sheetdb
import manage_time

# STEP 0: LOAD TOKEN FROM SOMEWHERE SAFE
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# STEP 1: BOT SETUP
intents: Intents = Intents.default()
intents.message_content = True  # NOQA # Aktiviert das Tracking von Nachrichteninhalten
intents.members = True  # NOQA # Ermöglicht das Tracking von Mitgliederereignissen
intents.voice_states = True  # NOQA # Ermögliche das Tracking von Voice Channel-Ereignissen
client = commands.Bot(command_prefix=".", intents=Intents.all())


async def send_message_to_log_channel(member, message):
    # Finde den Kanal "log" auf dem Server des Benutzers
    log_channel = None
    for channel in member.guild.text_channels:  # Durchsuche alle Textkanäle des Servers
        if 'log' in channel.name:  # Überprüfe, ob der Kanalname "log" ist
            log_channel = channel
            break

    # Sende die Nachricht, wenn der Kanal gefunden wurde
    if log_channel:
        await log_channel.send(message)
    else:
        print(f"No Log channel in {member.guild.name}")


# STEP 2: CALCULATE THE WORKING TIMES FOR ALL THE EMPLOYEES
user_times = {}


# CHECK IF USER IS IN VOICE CHANNEL
def is_user_in_voice(member):
    return member.voice is not None and member.voice.channel is not None


worked_time_string = ""
daily_flag = False


def calculate_working_hours(times, member):
    total_seconds = 0
    join_time = None
    was_in_voice = False
    now = manage_time.get_time()  # Assuming get_time() returns a datetime object

    if is_user_in_voice(member):
        times.append(('leave', now))
        was_in_voice = True
        print(f'user was in voice channel at {now} when calculate_working_hours was called')
    for status, time in times:
        if status == 'join':
            join_time = time
        elif status == 'leave' and join_time:
            total_seconds += (time - join_time).total_seconds()
            join_time = None

    if was_in_voice:
        times.pop()
        was_in_voice = False

    # Get expected time from sheet
    try:
        global daily_flag
        if daily_flag:
            now_minus_one_day = now - timedelta(days=1)
            expected_time = sheetdb.get_row_data_by_date(now_minus_one_day, member.display_name, 'should work for')
            daily_flag = False
        else:
            expected_time = sheetdb.get_row_data_by_date(now, member.display_name, 'should work for')
    except ValueError as e:
        expected_time = "00:00"
        print('Error while trying read sheet: ', e)

    # Convert expected time into string
    expected_time_string = manage_time.change_time_format(expected_time)
    # Convert expected time into seconds
    expected_time_seconds = manage_time.time_string_to_seconds(expected_time)

    # Calculate the gap
    gap_seconds = total_seconds - expected_time_seconds

    # Adjust the gap_sign based on the total seconds (positive or negative)
    gap_sign = "+" if gap_seconds >= 0 else "-"
    # Convert gap seconds into HHh MMm
    if gap_sign == "-":
        gap_string = manage_time.seconds_to_formatted_string(gap_seconds * -1)
    else:
        gap_string = manage_time.seconds_to_formatted_string(gap_seconds)

    # Convert worked time into HHh MMm
    global worked_time_string
    worked_time_string = manage_time.seconds_to_formatted_string(total_seconds)
    worked_time_formatted_string = manage_time.change_time_format(worked_time_string)

    embed = embedded.working_hours(member.mention, worked_time_formatted_string, manage_time.change_time_format(gap_string), expected_time_string, gap_sign)

    return embed


async def find_user_category(guild, user_name):
    lower_user_name = user_name.lower()
    for category in guild.categories:
        if lower_user_name in category.name.lower():
            return category
    return None


async def find_working_times_channel(category):
    for channel in category.text_channels:
        if 'working-times' in channel.name.lower():
            return channel
    return None


async def find_members_in_office():
    # Durchsuchen Sie alle Server (Guilds), in denen der Bot aktiv ist
    for guild in client.guilds:
        print(f'Guild: {guild}')
        # Durchsuchen Sie alle Voice-Channels auf dem Server
        for voice_channel in guild.voice_channels:
            print(f'Voice channel: {voice_channel}')
            # Durchsuchen Sie alle Mitglieder im Voice-Channel
            for member in voice_channel.members:
                if any(role.name == "in" for role in member.roles):
                    print(f'Member: {member}')
                    if is_user_in_voice(member):
                        print(f'{member} is in {voice_channel}')
                        # Wenn der Benutzer in einem Voice-Channel ist, fügen Sie die Join-Zeit hinzu
                        if member not in user_times:
                            print(f'adding {member} to working times database')
                            user_times[member] = []
                            user_times[member].append(('join', manage_time.get_time()))
                            sheetdb.sheet_add_time(member.display_name, "Started at", manage_time.get_time(), manage_time.get_time())


async def daily_report():
    while True:
        now = manage_time.get_time()
        # Setze target_time auf den Beginn des nächsten Tages (Mitternacht)
        # Zuerst wird der aktuelle Tag ohne Zeit genommen, dann ein Tag hinzugefügt und die Zeitzone berücksichtigt.
        target_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_target = (target_time - now).total_seconds()
        await asyncio.sleep(seconds_until_target)

        for guild in client.guilds:
            for member in guild.members:
                if 'in' in [role.name.lower() for role in member.roles]:
                    category = await find_user_category(guild, member.display_name)
                    if category:
                        working_times_channel = await find_working_times_channel(category)
                        if working_times_channel:
                            try:
                                # Check if the member is not in user_times or their times are empty
                                if member not in user_times:
                                    print(f'{member} not in user_times')
                                    await working_times_channel.send(f"{member.display_name} did not work today.")
                                else:
                                    for user_id, times in user_times.items():
                                        if user_id == member:
                                            global daily_flag
                                            daily_flag = True
                                            embed = calculate_working_hours(times, member)
                                            if embed:
                                                await working_times_channel.send(embed=embed)  # NOQA
                            except Exception as e:
                                await working_times_channel.send(f"Error during daily report: {e}")
                        else:
                            print(
                                f"Could not find 'working-times' Channel in the category {category.name} for the user {member.display_name}")
                    else:
                        print(f"Could not find category for {member.display_name}")

        user_times.clear()
        await find_members_in_office()


# STEP 3: HANDLING THE STARTUP FOR OUR BOT
@client.event
async def on_ready() -> None:
    await client.tree.sync()
    await client.change_presence(activity=CustomActivity('Watching you!'), status=Status.do_not_disturb)
    print(f'{client.user} is now running!')
    await find_members_in_office()
    asyncio.create_task(daily_report())  # NOQA


# STEP 4: HANDLING INCOMING MESSAGES WITH PREFIX
@client.command()
async def test_text_command(ctx):
    await ctx.send('Test successful')


@client.tree.command(name='ping', description='Pings the server')
async def ping(interaction: Interaction):
    bot_latency = round(client.latency * 1000)
    await interaction.response.send_message(f'Pinging!... {bot_latency}ms')  # NOQA


@client.tree.command(name='working_hours', description='Sums up the time spent in a Voice Channel today')
@app_commands.describe(member='Employee')
async def working_hours(interaction: Interaction, member: Member):
    embed = None
    print(f'{member} has used [/working_hours] in {interaction.channel}')
    await send_message_to_log_channel(member, f'{member.display_name} has used [/working_hours] in {interaction.channel.mention}')
    try:
        print('trying to get working hours')
        for user_id, times in user_times.items():
            if user_id == member:  # SEARCH FOR MENTIONED USER
                print(f'{member} found')
                # CALCULATES THE TOTAL HOURS OF THE MENTIONED USER
                embed = calculate_working_hours(times, member)
                break  # Beende die Schleife, da das Embed erstellt wurde
        if embed:
            await interaction.response.send_message(embed=embed)  # NOQA
        else:
            await interaction.response.send_message(f'{member.mention} did not work today')  # NOQA
    except Exception as e:
        await interaction.response.send_message(f'Error while trying /working_hours: {e}') # NOQA


@client.event
async def on_voice_state_update(member, before, after):
    if any(role.name == "in" for role in member.roles):
        user_category = await find_user_category(member.guild, member.display_name)

        if member not in user_times:
            user_times[member] = []

        # Determine the current category based on the new voice state
        current_category = after.channel.category if after.channel is not None else before.channel.category

        working_times_channel = await find_working_times_channel(user_category) if user_category else None

        try:
            # User switches voice channel without leaving (before.channel and after.channel are both not None and different)
            if before.channel is not None and after.channel is not None and before.channel != after.channel:
                print(f"{member} switched from {before.channel} to {after.channel}")

                # Handle leaving the previous channel
                leave_time = manage_time.get_time()  # Time user left the previous channel
                await log_voice_channel_change(member, before.channel, leave_time, 'Clocking Out', 'switched from', working_times_channel, current_category)

                # Handle joining the new channel
                join_time = leave_time  # Assuming switch happens instantaneously
                await log_voice_channel_change(member, after.channel, join_time, 'Clocking In', 'switched to', working_times_channel, current_category)

            # User joins a voice channel (and was not in one before)
            elif before.channel is None and after.channel is not None:
                await log_voice_channel_change(member, after.channel, manage_time.get_time(), 'Clocking In', 'joined', working_times_channel, current_category)

            # User leaves a voice channel (and does not join another one)
            elif before.channel is not None and after.channel is None:
                await log_voice_channel_change(member, before.channel, manage_time.get_time(), 'Clocking Out', 'left', working_times_channel, current_category)

        except errors.Forbidden:
            print(f"Missing permission to write in {working_times_channel.name}" if working_times_channel else "Missing permissions or working times channel not found")
    else:
        pass


async def log_voice_channel_change(member, voice_channel, time, status, action, working_times_channel, current_category):
    # Construct the embed message for the voice channel change
    embed = embedded.voice_channel_update(member.mention, voice_channel.mention, time, status, action)
    # Send the embed message to the working times channel
    if working_times_channel:
        await working_times_channel.send(embed=embed)
    # Log the event in the console
    print(f"{member.display_name} has {action} {voice_channel} in {current_category.name if current_category else 'no category'} at: {time}")
    # Log the action in the user's times
    action_type = 'join' if action in ['joined', 'switched to'] else 'leave'
    user_not_sheet = False
    if action_type == 'join' and not user_times[member]:
        user_not_sheet = True
    user_times[member].append((action_type, time))
    # Update the sheetdb with the time of the event
    if user_not_sheet:
        sheetdb.sheet_add_time(member.display_name, "Started at", manage_time.get_time(), time)
    else:
        # Only call calculate_working_hours and sheet_add_time when the user fully leaves a channel, not on switch
        if action == 'left':
            calculate_working_hours(user_times[member], member)
            sheetdb.sheet_add_time(member.display_name, "Finished at", manage_time.get_time(), time)
            sheetdb.sheet_add_time(member.display_name, "Worked for", manage_time.get_time(), worked_time_string)

    # Send a log message to a designated log channel
    await send_message_to_log_channel(member, f"{member.display_name} has {action} {voice_channel.name} at: {time.strftime('%d.%m.%y %H:%M')}")


# STEP 6: MAIN ENTRY POINT
def main() -> None:
    sheetdb.get_credentials()
    client.run(token=TOKEN)


if __name__ == '__main__':
    main()
