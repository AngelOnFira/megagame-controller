import axios from 'axios';

export function getTeams({ commit }) {
  axios.get(`http://localhost:8090/api/teams/`)
    .then(response => {
      commit('setTeams', response.data)
    })
}

export function addTeam({ commit }, name) {
  axios.post(`http://localhost:8090/api/teams/`, { name })
    .then(response => {
      commit('setTeams', response.data)
    })
}