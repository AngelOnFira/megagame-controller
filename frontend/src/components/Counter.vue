<template>
  <div class="card card-body m-4">
    <h3>Composition API + Vuex</h3>
    <h5 class="text-center">{{ counter2 }} x 3 = {{ times3 }}</h5>
    <button class="btn btn-primary" @click="inc">Increment</button>
  </div>
</template>

<script>
import { useState, useGetters, useMutations } from '../helpers'
import { computed } from 'vue'
import { useStore } from 'vuex'

export default {
  setup() {
    // const { counter2 } = useState(['counter2'])
    // const { times3 } = useGetters(['times3'])
    // const { increaseCounter } = useMutations(['increaseCounter'])

    // const inc = () => increaseCounter()
    // return { inc, counter2, times3 }

    // const store = useStore();
    const store = useStore()

    console.log(store);

    const counter2 = computed(() => store.state.messages.counter2);
    const times3 = computed(() => store.getters['messages/times3']);
    const inc = () => store.commit('messages/increaseCounter');

    return {
      counter2, times3, inc
    }
  }
}
</script>
