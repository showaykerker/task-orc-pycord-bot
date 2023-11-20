# Task Orc Pycord Bot

## Features
### Slash Commands
#### Trello

* `/trello get undone [me/all]`
* `/set_trello_list_to_trace`
* `/set_trello_board_list_to_create`

### Mentions
#### Forwarding Messages
#### Task Assignment
##### Description
The mention command listens for when you mention the bot in Discord in any channel. When you do, it will look at the message you send and try to create Trello cards from it.

##### Rules
* **Before Assigning Tasks**:
	* Set the Trello with command `/configure_trello`. A Trello key and Trello token must be prepared. You can generate them [here](https://developer.atlassian.com/cloud/trello/).
		* You will then need to manually assign each Trello member to the guild's member through a select menu.
	* The task will be automatically assigned to a trello board by comparing keywords in the message with keywords set in the bot. If no keywords are matched, the task will be assigned to the default board set in the bot. Use the command `/set_board_keyword` to set keywords for a board.
	* In each board, a list should be set to be the entrance of tasks created by the bot. Use the command `/set_trello_board_list_to_create` to set the entrance list.
* **Mention the bot**: Always mention the bot at the first line then go to the next line.
* **Optionally mention a member**: a line contains only member mentioned indicates that following lines of tasks are assigned to the member until another member is mentioned.
	* If everyone was mentioned, the following lines of tasks will be assigned to everyone.
* **Task Assignment**: Each line that contains no mentions will be a task.
	* **Due Date**: A task can be assigned with a due date or not. If not, the card will be created without due date. 
		* Here are compatible formats of date:
			1. a 4-digit MMDD number, which will be interpreted as the date of the nearest future, e.g. if today is 2021-12-25, `0128` will be interpreted as `2022-01-28`.
			2. a 6-digit YYMMDD number, which will be interpreted as the exact date.
			3. a 8-digit YYYYMMDD number, which will be interpreted as the exact date.
			4. a string with either one of `一二三四五六日` or `["Mo.", "Tu.", "We.", "Th.", "Fr.", "Sa.", "Su."]`, which will be interpreted as the date of the nearest future.
	* **Task Description**: The description of the task should be separated from the assigned date with a space if assigned
	* **Advanced Usage**: At the end of the task line, if you wish to overwrite the board that the task will be assigned to, you can mention the keyword that belongs to the target board with format `||keyword||`.

##### Usages
```
@Task Orc
@everyone
Click like button on all of our FB posts.
@showaykerker
Mo. Prepare for the meeting
1120 Compose the drum part of the new song
@brian.__.li
二 Create a new logo for the bot
Reply to the DMs
@alexandraQQ.
Handle the promotion of the album
四 New post on IG
```
See more usage examples [here](./task_assignment_usages.md).



## TODO

- [x] ~~Complete undone trello card command.~~ (23/11/09)
- [x] ~~Add a command to show all undone Trello cards assigned to a user.~~ (23/11/10)
- [x] ~~Modify trello configuring with an option to not pass in key and token.~~ (23/11/10)
- [x] ~~Show already set trello id table when re-configuring.~~ (23/11/10)
- [x] ~~Compare speed of getting interested cards between directly from requests to py-trello.~~ (Py-trello is faster)
- [x] ~~Add link to cards and link to all cards page.~~ (23/11/11)
- [x] ~~Add ChatGPT support for task assigning.~~ (ChatGPT not stable enough)
- [x] ~~UI to select Trello boards/ lists to get cards from.~~ (23/11/13)
- [x] Add UI to assign Trello board keywords.
- [x] ~~Use rule-based method to handle task assiging messages and turn it into a Trello cards.~~ (23/11/14)
- [x] ~~Overwrite assigned trello boards when assigning tasks.~~ (23/11/17)
- [ ] Time zone issue.
- [ ] Sort out weekday assignment issue.
- [ ] Add support for more time-assigning formats.
- [ ] Add support to assign task with a time.
- [ ] Figure out a way to show check lists in cards.
- [ ] Handle Trello ID configuring if members > 5.
- [ ] Handle Trello board keywords configuring if board > 5.
- [ ] Document.
- [ ] Make Trello key and token generation guide.
- [ ] Assign tasks to multiple, but not all, members.
- [ ] Refactor trello cogs.
- [ ] Refactor configuration process.
- [ ] Isolate configure command to another command group that can only be used by admins.