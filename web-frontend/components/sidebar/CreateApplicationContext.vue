<template>
  <Context>
    <ul class="context-menu">
      <li v-for="(application, type) in applications" :key="type">
        <a
          :ref="'createApplicationModalToggle' + type"
          @click="toggleCreateApplicationModal(type)"
        >
          <i
            class="context-menu-icon fas fa-fw"
            :class="'fa-' + application.iconClass"
          ></i>
          {{ application.name }}
        </a>
        <CreateApplicationModal
          :ref="'createApplicationModal' + type"
          :application="application"
          @created="hide"
        ></CreateApplicationModal>
      </li>
    </ul>
  </Context>
</template>

<script>
import { mapState } from 'vuex'

import CreateApplicationModal from '@/components/sidebar/CreateApplicationModal'
import context from '@/mixins/context'

export default {
  name: 'CreateApplicationContext',
  components: {
    CreateApplicationModal
  },
  mixins: [context],
  computed: {
    ...mapState({
      applications: state => state.application.applications
    })
  },
  methods: {
    toggleCreateApplicationModal(type) {
      const target = this.$refs['createApplicationModalToggle' + type][0]
      this.$refs['createApplicationModal' + type][0].toggle(target)
    }
  }
}
</script>
