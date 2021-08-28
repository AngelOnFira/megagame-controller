<template>
  <q-page padding>
    <Transactions />
  </q-page>

  <q-form @submit="onSubmit" class="q-gutter-md">
    <q-input
      filled
      v-model="currency_name"
      label="Currency *"
      hint="The name of the currency"
      lazy-rules
      :rules="[(val) => (val && val.length > 0) || 'Please type something']"
    />

    <q-input
      filled
      v-model="currency_emoji"
      label="Currency emoji *"
      hint="Emoji to show off for the currency"
      lazy-rules
      :rules="[(val) => (val && val.length > 0) || 'Please type something']"
    />

    <!-- <q-input
        filled
        type="number"
        v-model="age"
        label="Your age *"
        lazy-rules
        :rules="[
          val => val !== null && val !== '' || 'Please type your age',
          val => val > 0 && val < 100 || 'Please type a real age'
        ]"
        />-->

    <!-- <q-toggle v-model="accept" label="I accept the license and terms" /> -->

    <div>
      <q-btn label="Submit" type="submit" color="primary" />
      <q-btn label="Reset" type="reset" color="primary" flat class="q-ml-sm" />
    </div>
  </q-form>
</template>



<script>
// Import components transaction
import Transactions from "../components/Transactions";
import { ref } from "vue";

export default {
  name: "Bank",
  components: { Transactions },
  setup() {
    const currency_name = ref(null);
    const currency_emoji = ref(null);
    return {
      currency_name,
      currency_emoji,
      onSubmit() {
        store
          .dispatch("teams/createCurrency", {
            currency_name: currency_name.value,
            currency_emoji: currency_emoji.value,
          })
          .then(
            (response) => {
              $q.notify({
                color: "green-4",
                textColor: "white",
                icon: "cloud_done",
                message: "Submitted",
              });
            },
            (error) => {
              $q.notify({
                color: "red-5",
                textColor: "white",
                icon: "warning",
                message:
                  "There was an error creating the currency: " + error.message,
              });
              console.log(error);
            }
          );
      },
    };
  },
};
</script>
  