<template>
  <div class="card card-body m-4">
    <ul id="example-1">
      <li v-for="message in messages" :key="message.id">
        {{ message.member_username }}: {{ message.content }}
      </li>
    </ul>
  </div>
</template>

<script>
import { useState, useGetters, useMutations } from "../helpers";
import { computed } from "vue";
import { useStore } from "vuex";

export default {
  setup() {
    const store = useStore();

    const messages = computed(() => store.state.messages.messages);

    store.dispatch("messages/getMessages");

    return {
      messages,
    };
  },
};
</script>
