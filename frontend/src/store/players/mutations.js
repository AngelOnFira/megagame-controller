export default {
  SET_PLAYERS(state, players) {
    // if any players don't have discord_member, assign a default with an attribute of name
    for (const player of players) {
      player.message = ""
      if (!player.discord_member) {
        player.discord_member = { name: player.name };
      }
    }


    state.players = players
  },
}
