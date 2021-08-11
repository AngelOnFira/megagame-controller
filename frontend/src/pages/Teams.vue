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

      <q-card v-for="team in teams" :key="team.id">
        <q-card-section>
          <div class="text-h6">{{ team.name }}</div>
          <div class="p">{{ team.emoji }}</div>
        </q-card-section>
        <q-card-section>
          <div
            id="team-player-holder-{{team.id}}"
            @dragenter="onDragEnter"
            @dragleave="onDragLeave"
            @dragover="onDragOver"
            @drop="onDrop"
            class="drop-target rounded-borders overflow-hidden"
          >
            <q-card
              v-for="player in team.players"
              :key="player.id"
              :id="'player-' + player.id"
              draggable="true"
              @dragstart="onDragStart"
              class="box orange"
            >
              <q-card-section>
                <div class="text-h6">
                  {{ player_lookup[player.id].discord_member.name }}
                </div>
                <div class="p">test</div>
              </q-card-section>
            </q-card>
          </div>
        </q-card-section>
        <!-- <discord-picker
          input
          :value="value"
          gif-format="md"
          @update:value="value = $event"
          @emoji="setEmoji"
          @gif="setGif"
        /> -->
      </q-card>

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

    const teams = computed(() => store.state.teams.teams);
    const player_lookup = computed(() => store.state.players.player_lookup);

    const value = ref("");

    const status1 = ref([]);
    const status2 = ref([]);

    const status_obj = computed(() => {
      var status_obj = {};
      store.state.teams.teams.forEach((team) => {
        // It needs to be a ref so that it can be edited or something
        status_obj[team.id] = ref("");
      });
      return status_obj;
    });

    return {
      name,
      age,
      accept,
      teams,
      player_lookup,
      DiscordPicker,
      value,
      draggable,
      // handler(mutationRecords) {
      //   status1.value = [];
      //   for (const index in mutationRecords) {
      //     const record = mutationRecords[index];
      //     const info = `type: ${record.type}, nodes added: ${
      //       record.addedNodes.length > 0 ? "true" : "false"
      //     }, nodes removed: ${
      //       record.removedNodes.length > 0 ? "true" : "false"
      //     }, oldValue: ${record.oldValue}`;
      //     status1.value.push(info);
      //     // console.log(info);
      //   }
      // },
      // store the id of the draggable element
      onDragStart(e) {
        console.log(e);
        e.dataTransfer.setData("text", e.target.id);
        e.dataTransfer.dropEffect = "move";
      },
      onDragEnter(e) {
        // don't drop on other draggables
        if (e.target.draggable !== true) {
          e.target.classList.add("drag-enter");
        }
      },
      onDragLeave(e) {
        e.target.classList.remove("drag-enter");
      },
      onDragOver(e) {
        e.preventDefault();
      },
      onDrop(e) {
        e.preventDefault();
        // don't drop on other draggables
        if (e.target.draggable === true) {
          return;
        }
        const draggedId = e.dataTransfer.getData("text");
        const draggedEl = document.getElementById(draggedId);
        // check if original parent node
        if (draggedEl.parentNode === e.target) {
          e.target.classList.remove("drag-enter");
          return;
        }
        // make the exchange
        draggedEl.parentNode.removeChild(draggedEl);
        e.target.appendChild(draggedEl);
        e.target.classList.remove("drag-enter");
      },
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

<style scoped lang="sass">
.drop-target
  width: 200px
  height: 100px
  min-width: 200px
  background-color: gainsboro

.drag-enter
  outline-style: dashed

.box
  width: 100px
  height: 100px
  float: left
  cursor: pointer

@media only screen and (max-width: 500px)
  .drop-target
    height: 200px
    width: 100px
    min-width: 100px
    background-color: gainsboro

  .box
    width: 50px
    height: 50px

.box:nth-child(3)
  clear: both

.navy
  background-color: navy

.red
  background-color: firebrick

.green
  background-color: darkgreen

.orange
  background-color: orange
</style>
