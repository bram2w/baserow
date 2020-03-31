<template>
  <Context>
    <ul class="context-menu">
      <li v-for="(applicationType, type) in applications" :key="type">
        <a
          :ref="'createApplicationModalToggle' + type"
          @click="toggleCreateApplicationModal(type)"
        >
          <i
            class="context-menu-icon fas fa-fw"
            :class="'fa-' + applicationType.iconClass"
          ></i>
          {{ applicationType.name }}
        </a>
        <CreateApplicationModal
          :ref="'createApplicationModal' + type"
          :application-type="applicationType"
          @created="hide"
        ></CreateApplicationModal>
      </li>
    </ul>
  </Context>
</template>

<script>
import { mapState } from 'vuex'

import CreateApplicationModal from '@baserow/modules/core/components/application/CreateApplicationModal'
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'CreateApplicationContext',
  components: {
    CreateApplicationModal,
  },
  mixins: [context],
  computed: {
    ...mapState({
      applications: (state) => state.application.types,
    }),
  },
  methods: {
    toggleCreateApplicationModal(type) {
      const target = this.$refs['createApplicationModalToggle' + type][0]
      this.$refs['createApplicationModal' + type][0].toggle(target)
    },
  },
}
</script>
