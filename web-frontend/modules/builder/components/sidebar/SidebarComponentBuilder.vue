<template>
  <div>
    <SidebarApplication
      ref="sidebarApplication"
      :group="group"
      :application="application"
      @selected="selected"
    >
      <template #context>
        <li
          v-if="
            $hasPermission(
              'application.update',
              application,
              application.group.id
            )
          "
        >
          <a @click="settingsClicked">
            <i class="context__menu-icon fas fa-fw fa-cog"></i>
            {{ $t('sidebarComponentBuilder.settings') }}
          </a>
        </li>
      </template>
    </SidebarApplication>
    <BuilderSettingsModal ref="builderSettingsModal"></BuilderSettingsModal>
  </div>
</template>

<script>
import SidebarApplication from '@baserow/modules/core/components/sidebar/SidebarApplication'
import BuilderSettingsModal from '@baserow/modules/builder/components/settings/BuilderSettingsModal'

export default {
  name: 'TemplateSidebar',
  components: { BuilderSettingsModal, SidebarApplication },
  props: {
    application: {
      type: Object,
      required: true,
    },
    group: {
      type: Object,
      required: true,
    },
  },
  methods: {
    selected() {
      console.log('TODO')
    },
    settingsClicked() {
      this.$refs.sidebarApplication.$refs.context.hide()
      this.$refs.builderSettingsModal.show()
    },
  },
}
</script>
