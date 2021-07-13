<template>
  <div class="card card-body m-4">
    <!-- A header that says transactions -->

    <div class="row">
      <div class="col-12">
        <h4 class="text-center">Transactions</h4>
      </div>
    </div>
    <!-- A list of transactions in boxes -->
    <div class="q-pa-md" style="max-width: 350px">
      <q-list>
        <q-item v-for="transaction in transactions" :key="transaction.id">
          <q-item-section>
            <q-item-label
              >{{ transaction.from_wallet.name }} ->
              {{ transaction.to_wallet.name }}</q-item-label
            >
            <q-item-label caption lines="2"
              >{{ transaction.amount }}
              {{ transaction.currency.name }}</q-item-label
            >
          </q-item-section>
          <q-item-section side top>
            <q-item-label caption>{{ transaction.elapsed }}</q-item-label>
            <q-icon name="star" color="yellow" />
          </q-item-section>
        </q-item>
      </q-list>
    </div>
  </div>
</template>

<script>
import { computed } from "vue";
import { useStore } from "vuex";

export default {
  setup() {
    const store = useStore();

    const transactions = computed(() => store.state.bank.transactions);

    store.dispatch("bank/getTransactions");

    return {
      transactions,
    };
  },
};
</script>
