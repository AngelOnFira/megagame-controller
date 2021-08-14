import axios from 'axios';

export function getTeams({ commit }) {
  axios.get(`http://localhost:8090/api/teams/`)
    .then(response => {
      commit('setTeams', response.data)
    })
}

export function createTeam({ commit }, { team_name, team_emoji }) {
  return new Promise((resolve, reject) => {
    axios.post(`http://localhost:8090/api/teams/`, { name: team_name, emoji: team_emoji })
      .then(response => {
        // If the request was successful, add the team to the store
        commit('addTeamToState', response.data)

        resolve(response);
      }, (error) => {
        reject(error);
      })
  })
}