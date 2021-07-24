export default {
  setTeams(state, teams) {
    state.teams = teams
  },

  addTeamToState(state, team) {
    state.teams.push(team)
  }
}
