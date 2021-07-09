import { store } from 'quasar/wrappers'
import { createStore } from 'vuex'

import messages from './messages'
import bank from './bank'


export default createStore({
  modules: {
    messages,
    bank
  },

  // enable strict mode (adds overhead!)
  // for dev mode and --debug builds only
  strict: process.env.DEBUGGING
})