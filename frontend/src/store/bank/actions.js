import axios from 'axios';

export function getTransactions({ commit }) {
  axios.get(`http://localhost:8090/api/transactions/`)
    .then(response => {
      commit('setTransactions', response.data)

      setInterval(() => {
        commit('setElapsedTimes')
      }, 1000)
    })
}

export function createCurrency({ commit }, { currencies_name, currencies_emoji }) {
  return new Promise((resolve, reject) => {
    axios.post(`http://localhost:8090/api/currencies/`, { name: currencies_name, emoji: currencies_emoji })
      .then(response => {
        // If the request was successful, add the currencies to the store
        commit('addCurrencyToState', response.data)

        resolve(response);
      }, (error) => {
        reject(error);
      })
  })
}