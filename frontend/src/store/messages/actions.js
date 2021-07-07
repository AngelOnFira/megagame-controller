import axios from 'axios';

export function getMessages({ commit }) {
  axios.get(`http://localhost:8090/api/stats/`)
    .then(response => {
      console.log("here");
      commit('setMessages', response.data)
    })
}

