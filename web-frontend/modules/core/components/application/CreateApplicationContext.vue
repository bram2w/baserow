<template>
  <Context>
    <ul class="context__menu">
      <li v-for="(applicationType, type) in applications" :key="type">
        <a
          :ref="'createApplicationModalToggle' + type"
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
        <a @click=";[$refs.templateModal.show(), hide()]">
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
  },
  methods: {
    toggleCreateApplicationModal(type) {
      const target = this.$refs['createApplicationModalToggle' + type][0]
      this.$refs['createApplicationModal' + type][0].toggle(target)
      this.hide()
    },
  },
}
</script>

<i18n>
{
  "en": {
    "createApplicationContext":{
      "fromTemplate": "From template"
    }
  },
  "fr": {
    "createApplicationContext":{
      "fromTemplate": "À partir d'un modèle"
    }
  }
}
</i18n>
