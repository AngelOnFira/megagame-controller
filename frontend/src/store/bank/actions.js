import axios from 'axios';

export function getTransactions({ commit }) {
  axios.get(`http://localhost:8090/api/transactions/`)
    .then(response => {
      commit('setTransactions', response.data)
    })
}

