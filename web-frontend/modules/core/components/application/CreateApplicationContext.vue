<template>
  <Context @shown="fetchRolesAndPermissions">
    <div
      v-if="group._.additionalLoading"
      class="loading margin-left-2 margin-top-2 margin-right-2 margin-bottom-2"
    ></div>
    <ul v-else class="context__menu">
      <li v-for="(applicationType, type) in applications" :key="type">
        <a
          :ref="'createApplicationModalToggle' + type"
          :class="{
            disabled: !canCreateCreateApplication,
          }"
          @click="toggleCreateApplicationModal(type)"
        >
          <i
            class="context__menu-icon fas fa-fw"
            :class="'fa-' + applicationType.iconClass"
          ></i>
          {{ applicationType.getName() }}
        </a>
        <CreateApplicationModal
          :ref="'createApplicationModal' + type"
          :application-type="applicationType"
          :group="group"
          @created="hide"
        ></CreateApplicationModal>
      </li>
      <li>
        <a
          :class="{
            disabled: !canCreateCreateApplication,
          }"
          @click="openTemplateModal()"
        >
          <i class="context__menu-icon fas fa-fw fa-file-alt"></i>
          {{ $t('createApplicationContext.fromTemplate') }}
        </a>
        <TemplateModal ref="templateModal" :group="group"></TemplateModal>
      </li>
    </ul>
  </Context>
</template>

<script>
import CreateApplicationModal from '@baserow/modules/core/components/application/CreateApplicationModal'
import TemplateModal from '@baserow/modules/core/components/template/TemplateModal'
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'CreateApplicationContext',
  components: {
    CreateApplicationModal,
    TemplateModal,
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
    canCreateCreateApplication() {
      return this.$hasPermission(
        'group.create_application',
        this.group,
        this.group.id
      )
    },
  },
  methods: {
    async fetchRolesAndPermissions() {
      await this.$store.dispatch('group/fetchPermissions', this.group)
      await this.$store.dispatch('group/fetchRoles', this.group)
    },
    openTemplateModal() {
      if (!this.canCreateCreateApplication) {
        return
      }

      this.$refs.templateModal.show()
      this.hide()
    },
    toggleCreateApplicationModal(type) {
      if (!this.canCreateCreateApplication) {
        return
      }

      const target = this.$refs['createApplicationModalToggle' + type][0]
      this.$refs['createApplicationModal' + type][0].toggle(target)
      this.hide()
    },
  },
}
</script>
