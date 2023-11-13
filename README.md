# Task Orc Pycord Bot

## Features
### Slash Commands
#### Trello
* `/trello get undone [me/all]`
* `/set_trello_list_to_trace`
* `/set_trello_board_list_to_create`

## TODO

- [x] ~~Complete undone trello card command.~~ (23/11/09)
- [x] ~~Add a command to show all undone Trello cards assigned to a user.~~ (23/11/10)
- [x] ~~Modify trello configuring with an option to not pass in key and token.~~ (23/11/10)
- [x] ~~Show already set trello id table when re-configuring.~~ (23/11/10)
- [x] ~~Compare speed of getting interested cards between directly from requests to py-trello.~~ (Py-trello is faster)
- [x] ~~Add link to cards and link to all cards page.~~ (23/11/11)
- [x] ~~Add ChatGPT support for task assigning.~~ (ChatGPT not stable enough)
- [x] ~~UI to select Trello boards/ lists to get cards from.~~ (23/11/13)
- [ ] Figure out a way to show check lists in cards.
- [ ] Use rule-based method to handle task assiging messages and turn it into a Trello cards.
- [ ] Handle Trello ID congifuring if members > 5.
- [ ] Isolate configure command to another command group that can only be used by admins.