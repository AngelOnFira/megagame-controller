<template>
  <q-page padding>
    <div class="q-pa-md row items-start q-gutter-md">
      <q-card
        class="my-card full-width"
        v-for="player in players"
        :key="player.id"
      >
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">{{ player.name || "Unknown" }}</div>
          <div class="text-subtitle2">{{ player.discord_member.name }}</div>
        </q-card-section>

        <q-card-section class="bg-primary text-white">
          <q-input standout v-model="form[player.id].value" label="Message" />
          <q-btn
            color="secondary"
            label="Send"
            @click="handleSend(player.id, form[player.id].value)"
          />
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script>
import { computed } from "vue";
import { useStore } from "vuex";
import { ref } from "vue";

export default {
  setup() {
    const store = useStore();

    const players = computed(() => store.state.players.players);
    const form = computed(() => {
      var form = {};
      store.state.players.players.forEach((player) => {
        // It needs to be a ref so that it can be edited or something
        form[player.id] = ref("");
      });
      return form;
    });

    const handleSend = (playerId, message) => {
      console.log(playerId, message);
      store.dispatch("players/sendMessage", { playerId, message });
    };

    return {
      players,
      form,
      handleSend,
    };
  },
};
</script>
