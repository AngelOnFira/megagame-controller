import axios from 'axios';

export function getPlayers({ commit }) {
  axios.get(`http://localhost:8090/api/players/`)
    .then(response => {
      commit('SET_PLAYERS', response.data)
    })
}

export function sendMessage({ commit }, { playerId, message }) {
  axios.post(`http://localhost:8090/api/players/send-message/`, { playerId, message })
    .then(response => {
      commit('SET_MESSAGES', response.data)
    })
}

export function changeTeam({ commit }, { playerId, teamId }) {
  axios.post(`http://localhost:8090/api/players/change-team/`, { playerId, teamId })
    .then(response => {
      commit('SET_PLAYERS', response.data)
    })
}