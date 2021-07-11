export default {
  setTransactions(state, transactions) {
    state.transactions = transactions
  },

  setElapsedTimes(state) {
    // Go through each transaction in state.transactions and find the time elapsed since it's
    // completed_date (which is a datetime string) and add it to the transaction object in the following form:
    // 
    // - In seconds if it's less than a minute
    // - In minutes if it's less than an hour
    // - In hours if it's more than an hour
    // 
    // Format each as an integer, and add the time unit
    state.transactions.map(transaction => {
      const elapsedTime = (Date.now() - new Date(transaction.completed_date).getTime()) / 1000
      if (elapsedTime < 60) {
        transaction.elapsed = parseInt(elapsedTime) + 's'
      } else if (elapsedTime < 60 * 60) {
        transaction.elapsed = parseInt(elapsedTime / 60) + 'mins'
      } else {
        transaction.elapsed = parseInt(elapsedTime / (60 * 60)) + 'hrs'
      }
    })
  }
}
