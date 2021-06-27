<template>
  <div>
    <p>{{ title }}</p>
    <ul>
      <li v-for="message in messages" :key="message.discord_id">
        {{ message.member_username }} - {{ message.content }}
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
import {
  defineComponent,
  PropType,
  computed,
  ref,
  toRef,
  Ref,
} from '@vue/composition-api';
import { api } from 'boot/axios'
import { Message } from './models';
import { useQuasar } from 'quasar'

export default defineComponent({
  name: 'MessageComponent',
  props: {
    messages: {
      type: Array as unknown as PropType<Message[]>,
      default: () => [],
    },
  },
  setup(props) {
    const $q = useQuasar()
    // let data: Message = {} as Message;

    function loadData () {
      api.get<Message[]>('/api/backend')
        .then((response) => {
          props.messages = response.data
        })
        .catch(() => {
          $q.notify({
            color: 'negative',
            position: 'top',
            message: 'Loading failed',
            icon: 'report_problem'
          })
      })
    }
    return {loadData};
  }
});
</script>