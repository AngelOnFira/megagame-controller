<template>
  <div class="card card-body m-4">
    <ul id="example-1">
      <li v-for="transaction in transactions" :key="transaction.id">
        {{ transaction.from_wallet.name }}: {{ transaction.to_wallet.name }}
        {{ transaction.amount }} {{ transaction.currency.name }}
      </li>
    </ul>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'

export default {
  setup() {
    const store = useStore()

    const transactions = computed(() => store.state.bank.transactions);

    store.dispatch('bank/getTransactions');

    return {
      transactions
    }
  }
}
</script>
