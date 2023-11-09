# Task Orc Pycord Bot

## Features
### Slash Commands
#### Trello
* `/trello get undone [me/all]`

## TODO

- [x] Complete undone trello card command.
- [x] Add a command to show all undone Trello cards assigned to a user.
- [ ] Modify trello configuring with an option to not pass in key and token.
- [ ] Figure out a way to show check lists in cards.
- [ ] Add ChatGPT support for task assigning.
- [x] ~~Compare speed of getting interested cards between directly from requests to py-trello.~~ (Py-trello is faster)
- [ ] UI to select Trello boards/ lists to get cards from.
- [ ] Handle Trello ID congifuring if members > 5.
- [ ] Isolate configure command to another command group that can only be used by admins.