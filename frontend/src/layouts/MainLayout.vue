<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title> Megagame Controller </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered class="bg-grey-1">
      <q-list>
        <EssentialLink
          v-for="link in essentialLinks"
          :key="link.title"
          v-bind="link"
        />
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import EssentialLink from "components/EssentialLink.vue";
import Counter from "components/Counter.vue";

const linksList = [
  {
    title: "Bank",
    caption: "",
    icon: "",
    link: "/#/bank",
  },
  {
    title: "Teams",
    caption: "",
    icon: "",
    link: "/#/teams",
  },
  {
    title: "Players",
    caption: "",
    icon: "",
    link: "/#/players",
  },
];

import { defineComponent, ref } from "vue";
import { Loading } from "quasar";

export default defineComponent({
  name: "MainLayout",

  components: {
    EssentialLink,
  },

  // Fill up the store
  preFetch({ store }) {
    Loading.show();

    const players_promise = store.dispatch("players/getPlayers");
    const teams_promise = store.dispatch("teams/getTeams");
    const transations_promise = store.dispatch("bank/getTransactions");

    return Promise.all([
      players_promise,
      teams_promise,
      transations_promise,
    ]).then(() => {
      Loading.hide();
    });
  },

  setup() {
    const leftDrawerOpen = ref(false);

    return {
      essentialLinks: linksList,
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
      },
    };
  },
});
</script>
