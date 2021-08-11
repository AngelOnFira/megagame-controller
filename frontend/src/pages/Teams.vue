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

      <q-card-section v-for="team in teams" :key="team.id">
        <div class="text-h6">{{ team.name }}</div>
        <div class="p">{{ team.emoji }}</div>
        <q-card-section v-for="player in team.players" :key="player.id">
          <div class="text-h6">{{ player.name }}</div>
          <div class="p">test</div>
        </q-card-section>
        <!-- <discord-picker
          input
          :value="value"
          gif-format="md"
          @update:value="value = $event"
          @emoji="setEmoji"
          @gif="setGif"
        /> -->
      </q-card-section>

      <!-- <draggable
        v-model="myArray"
        group="people"
        @start="drag = true"
        @end="drag = false"
        item-key="id"
      >
        <template #item="{ element }">
          <div>{{ element.name }}</div>
        </template>
      </draggable> -->
    </div>
  </q-page>
</template>

<script>
import { useQuasar } from "quasar";
import { ref } from "vue";
import { computed } from "vue";
import { useStore } from "vuex";
import DiscordPicker from "vue3-discordpicker";
import draggable from "vuedraggable";

export default {
  setup() {
    const $q = useQuasar();
    const name = ref(null);
    const age = ref(null);
    const accept = ref(false);
    const store = useStore();

    store.dispatch("teams/getTeams");

    const teams = computed(() => store.state.teams.teams);

    const value = ref("");

    const myArray = [
      {
        name: "Jesus",
        id: 1,
      },
      {
        name: "Paul",
        id: 2,
      },
      {
        name: "Luc",
        id: 5,
      },
      {
        name: "Peter",
        id: 3,
      },
    ];

    return {
      name,
      age,
      accept,
      teams,
      DiscordPicker,
      value,
      draggable,
      myArray,
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
      setEmoji(emoji) {
        console.log(emoji);
      },
      setGif(gif) {
        console.log(gif);
      },
    };
  },
};
</script>
