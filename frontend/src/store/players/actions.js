import axios from 'axios';

export function getPlayers({ commit }) {
  axios.get(`http://localhost:8090/api/players/`)
    .then(response => {
      commit('SET_PLAYERS', response.data)
    })
}
