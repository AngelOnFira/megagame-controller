import axios from 'axios';

export function getTeams({ commit }) {
  axios.get(`http://localhost:8090/api/teams/`)
    .then(response => {
      commit('setTeams', response.data)
    })
}

export function addTeam({ commit }, name) {
  return new Promise((resolve, reject) => {
    axios.post(`http://localhost:8090/api/teams/`, { name })
      .then(response => {
        // If the request was successful, add the team to the store
        commit('addTeams', response.data)

        resolve(response);
      }, (error) => {
        reject(error);
      })
  })
}