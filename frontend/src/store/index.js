import { store } from 'quasar/wrappers'
import { createStore } from 'vuex'

import messages from './messages'
import bank from './bank'
import teams from './teams'


export default createStore({
  modules: {
    messages,
    bank,
    teams,
  },

  // enable strict mode (adds overhead!)
  // for dev mode and --debug builds only
  strict: process.env.DEBUGGING
})