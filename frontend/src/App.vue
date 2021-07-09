<template>
  <div class="container">
    <Counter />
    <Transactions />
  </div>
</template>

<script>
import Counter from './components/Counter.vue'
import Transactions from './components/Transactions.vue'

export default {
  name: 'App',
  components: { Counter, Transactions }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
