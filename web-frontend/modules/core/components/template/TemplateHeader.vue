<template>
  <div class="templates__header">
    <template v-if="template !== null">
      <div class="templates__icon">
        <i class="fas" :class="'fa-' + template.icon"></i>
      </div>
      <div class="templates__header-title">
        {{ template.name }}
        <small v-if="category !== null">{{ category.name }}</small>
      </div>
      <div class="templates__install">
        <a
          class="button"
          :class="{ 'button--loading': installing }"
          @click="install(template)"
          >{{ $t('templateHeader.use') }}</a
        >
      </div>
    </template>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import TemplateService from '@baserow/modules/core/services/template'

export default {
  name: 'TemplateHeader',
  props: {
    group: {
      type: Object,
      required: true,
    },
    template: {
      required: true,
      validator: (prop) => typeof prop === 'object' || prop === null,
    },
    category: {
      required: true,
      validator: (prop) => typeof prop === 'object' || prop === null,
    },
  },
  data() {
    return {
      installing: false,
    }
  },
  methods: {
    async install(template) {
      this.installing = true

      try {
        const { data } = await TemplateService(this.$client).install(
          this.group.id,
          template.id
        )
        // Installing a template has just created a couple of applications in the
        // group. The response contains those applications and we can add them to the
        // store so that the user can view the installed template right away.
        data.forEach((application) => {
          this.$store.dispatch('application/forceCreate', application)
        })
        if (data.length > 0) {
          // If there are applications, we want to select the first one right away.
          const application = this.$store.getters['application/get'](data[0].id)
          const type = this.$registry.get('application', application.type)
          type.select(application, this)
        }
        this.$emit('installed')
      } catch (error) {
        notifyIf(error, 'template')
        this.installing = false
      }
    },
  },
}
</script>

<i18n>
{
  "en": {
    "templateHeader": {
      "use": "Use this template"
    }
  },
  "fr": {
    "templateHeader": {
      "use": "Utiliser ce modèle"
    }
  }
}
</i18n>
