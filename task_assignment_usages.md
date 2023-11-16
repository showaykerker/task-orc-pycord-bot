# Task Assignment Usages

## Simple Task Creation
This will create a Trello card with title `Update project documentation`, which has no due date and no asignee.
```
@Task Orc
Update project documentation
```

## Assigning Tasks with Due Dates
This will create Trello cards:
1. with title `Celebrate the day` with due date `2024/01/28` and no assignee.
2. with title `Go shopping` with the nearest Sunday in the future as due date and no assignee.
3. with title `Read the book` with the nearest Monday in the future as due date and no assignee.
```
@Task Orc
240128 Celebrate the day.
日 Go shopping
Mo. Read the book
```

## Assigning Tasks to Specific Members:
This will create Trello cards:
1. with title `Design new logo` with no due date and assigned to Alice.
2. with title `Create branding strategy` with no due date and assigned to Alice.
3. with title `Test new software feature` with due date `2023/11/20` (assuming it's 2023/11/17 today) and assigned to Shoawykerker.
```
@Task Orc
@Alice
Design new logo
Create branding strategy
@shoawykerker
1120 Test new software feature
```

## Assigning Tasks to Everyone:
This will create Trello cards:
1. with title `General meeting preparation` with no due date and assigned to everyone.
2. with title `Update project status` with no due date and assigned to everyone.
3. with title `GO TO THE GYM` with the nearest Monday as due date and assigned to showaykerker.
4. with title `Complete the bot` with the nearest Friday as due date and assigned to showaykerker.
```
@Task Orc
@everyone
General meeting preparation
Update project status
@showaykerker
Mo. GO TO THE GYM
五 Complete the bot
```

## Overwriting Board Assignment:
This will create Trello cards:
1. with title `Plan marketing campaign` with no due date and no assinee, and assign to the board you set with keyword `IG`
2. with title `Research competitor products` with no due date and no assinee, and assign to the board without keywords.
2. with title `Take a look at the new logo` with no due date and no assinee, and assign to the board without keywords.
```
@TrelloBot
Plan marketing campaign ||IG||
Research competitor products ||default||
Take a look at the new logo ||||
```
