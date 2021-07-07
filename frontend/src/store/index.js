import { store } from 'quasar/wrappers'
import { createStore } from 'vuex'

import messages from './messages'


export default createStore({
  modules: {
    messages
  },

  // enable strict mode (adds overhead!)
  // for dev mode and --debug builds only
  strict: process.env.DEBUGGING
})