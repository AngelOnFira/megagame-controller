<template>
  <q-page padding>
    <div class="q-pa-md" style="max-width: 400px">
      <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
        <q-input
          filled
          v-model="name"
          label="Your name *"
          hint="Name and surname"
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
          <q-btn
            label="Reset"
            type="reset"
            color="primary"
            flat
            class="q-ml-sm"
          />
        </div>
      </q-form>
    </div>
  </q-page>
</template>

<script>
import { useQuasar } from "quasar";
import { ref } from "vue";
import { computed } from "vue";
import { useStore } from "vuex";
export default {
  setup() {
    const $q = useQuasar();
    const name = ref(null);
    const age = ref(null);
    const accept = ref(false);
    const store = useStore();

    store.dispatch("teams/getTeams");

    return {
      name,
      age,
      accept,
      onSubmit() {
        if (accept.value !== true && 1 == 2) {
          $q.notify({
            color: "red-5",
            textColor: "white",
            icon: "warning",
            message: "You need to accept the license and terms first",
          });
        } else {
          store
            .dispatch("teams/addTeam", {
              name: name.value,
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
                    "There was an error creating the team: " + error.message,
                });
                console.log(error);
              }
            );
        }
      },
      onReset() {
        name.value = null;
        age.value = null;
        accept.value = false;
      },
    };
  },
};
</script>
