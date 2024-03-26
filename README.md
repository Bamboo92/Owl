# README for Discord Time Tracking Bot

## Overview
This Discord bot is designed to track the working hours of users within a Discord server, leveraging voice channel activities as the primary mechanism for time tracking. It's especially useful for remote teams or communities where members' participation or working hours need to be monitored and recorded. The bot integrates with Google Sheets for data storage, providing a straightforward way to manage and visualize time tracking data.

### Features
- **Role-Based Activation**: Only users with the "in" role are tracked, ensuring that the bot's activities are focused and manageable.
- **Personalized Data Storage**: Each tracked user must have a Discord category that includes their name, and within this category, a text channel named "working-times" where the bot sends embedded messages specific to their activities.
- **Voice Channel Monitoring**: The bot monitors when a user joins, leaves, or switches between voice channels on the server.
- **Time Tracking**: The bot records the first join time of the day in a Google Sheet under the column named after the user plus "Started at" for the respective date. It updates the "Finished at" time and total working time whenever the user leaves a voice channel.
- **Command for Working Hours**: The `working_hours` command calculates and displays the worked time for a specified user, adjusting for the current presence in a voice channel if applicable.
- **Daily Reports**: Generates a daily report at midnight (00:00), summarizing each user's working hours for the day in their respective "working-times" text channel.
- **Error Handling**: If there's an error reading the required time from the sheet, it defaults to "00:00".

### Setup Requirements
To use this bot effectively, ensure the following:
- The Discord user to be tracked has the "in" role.
- The user has a Discord category named after them containing a text channel named "working-times".
- The bot has permissions to read voice channel events and send messages in the server.

### How It Works
1. **Tracking Start/End Times**: When a user with the "in" role joins a voice channel, their start time is logged. When they leave, the bot logs their end time and calculates the total working time for the day.
2. **Switching Channels**: If a user switches channels, a message is sent to the text channel, but the sheet is not updated. Internal timestamps are kept for join and leave events.
3. **Using `working_hours` Command**: This command calculates the worked hours for the user, comparing it against the "should work for" time specified in the Google Sheet. It shows whether the user has overworked or underworked, displaying the difference accordingly.
4. **Daily Reports**: At midnight, the bot sends out a report for each user, summarizing the day's working hours in their respective "working-times" text channel.
5. **Data Storage**: User times are stored in a Google Sheet, with key events logged to ensure data integrity and ease of management. After the daily report, the bot's internal storage is cleared to start fresh the next day.

### Installation
1. Clone this repository to your server.
2. Install required dependencies using `pip install -r requirements.txt`.
3. Configure your `.env` file with the `DISCORD_TOKEN` and `SPREADSHEET_ID` from your Discord bot and Google Sheets API credentials respectively.
4. Run the bot using `python bot.py`.

### Contribution
Contributions are welcome! If you'd like to improve the bot or add new features, please fork the repository and submit a pull request.

### Examples
Daily Report
<img width="207" alt="Screenshot_10" src="https://github.com/Bamboo92/Owl/assets/75183449/3d440cee-f922-4b29-96ac-d53392c22d2f">
<img width="263" alt="Screenshot_11" src="https://github.com/Bamboo92/Owl/assets/75183449/345c5095-a660-4192-9241-324cfd2733d3">
