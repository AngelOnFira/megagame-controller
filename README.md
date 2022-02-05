# Megagame Controller

This is a Discord bot created for megagames. The current iteration is written in
Discord.py/Django, with an incomplete web frontend written in Quasar (Vue.js).

## Features

### Trades

Teams can create trades to exchange any currencies that they have. This normally
comes down to a certain amount of the primary currency for some other
currencies. Teams must both accept the trade before it's completed.

<p align="center">
  <img src="https://media.discordapp.net/attachments/761253965349781532/939563234653003776/unknown.png" />
</p>

### Military Action

During turns in game, the control team can set up "payments", which require
teams to pay a certain amount of the primary currency for some action.

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/761253965349781532/939569347821719612/unknown.png" />
</p>

### UN Decisions

Similar to the military actions, the control team can set create custom payments
for more custom action in the game. This can happen in channels that are only
visible for certain roles on each team.

<p align="center">
  <img src="https://cdn.discordapp.com/attachments/761253965349781532/939569546807894046/unknown.png" />
</p>

## Future

I will be rewriting this project in Rust. Dealing with async Discord.py + sync
Django caused a lot of issues, and Discord.py is no longer maintained. You'll
see that there are many occurences of `@sync_to_async` and `@async_to_sync` in
the codebase. It makes it even more difficult to maintain type knowledge across
these transitions. Rust will help prevent many bugs while the bot is running,
while these had to be iterated on many times with Python.
