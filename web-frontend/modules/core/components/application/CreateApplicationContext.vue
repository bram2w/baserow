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
          :group="group"
          @created="hide"
        ></CreateApplicationModal>
      </li>
    </ul>
  </Context>
</template>

<script>
import CreateApplicationModal from '@baserow/modules/core/components/application/CreateApplicationModal'
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'CreateApplicationContext',
  components: {
    CreateApplicationModal,
  },
  mixins: [context],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  computed: {
    applications() {
      return this.$registry.getAll('application')
    },
  },
  methods: {
    toggleCreateApplicationModal(type) {
      const target = this.$refs['createApplicationModalToggle' + type][0]
      this.$refs['createApplicationModal' + type][0].toggle(target)
    },
  },
}
</script>
