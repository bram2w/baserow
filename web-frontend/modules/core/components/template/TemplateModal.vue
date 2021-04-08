<template>
  <Modal :full-screen="true" :close-button="false">
    <div v-if="loading" class="loading-absolute-center"></div>
    <template v-else>
      <TemplateHeader
        :group="group"
        :template="selectedTemplate"
        :category="selectedTemplateCategory"
        @installed="hide()"
      ></TemplateHeader>
      <TemplateCategories
        ref="categories"
        :categories="categories"
        :selected-template="selectedTemplate"
        @selected="selectTemplate"
      >
        <a class="modal__close" @click="hide()">
          <i class="fas fa-times"></i>
        </a>
      </TemplateCategories>
      <TemplateBody :template="selectedTemplate"></TemplateBody>
    </template>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import TemplateService from '@baserow/modules/core/services/template'
import { notifyIf } from '@baserow/modules/core/utils/error'

import TemplateHeader from '@baserow/modules/core/components/template/TemplateHeader'
import TemplateCategories from '@baserow/modules/core/components/template/TemplateCategories'
import TemplateBody from '@baserow/modules/core/components/template/TemplateBody'

export default {
  name: 'TemplateModal',
  components: { TemplateHeader, TemplateCategories, TemplateBody },
  mixins: [modal],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: true,
      categories: [],
      selectedTemplate: null,
      selectedTemplateCategory: null,
    }
  },
  methods: {
    /**
     * When the modal is opened we want to fetch all the templates and their
     * categories. They will be placed in the sidebar so that the user can select a
     * template to preview.
     */
    async show(...args) {
      modal.methods.show.call(this, ...args)

      this.loading = true
      this.categories = []
      this.selectedTemplate = null
      this.selectedTemplateCategory = null

      try {
        const { data } = await TemplateService(this.$client).fetchAll()
        this.categories = data
        this.loading = false
      } catch (error) {
        notifyIf(error, 'templates')
        this.hide()
      }

      // Check if there is a default template, and if so select that template.
      for (let i = 0; i < this.categories.length; i++) {
        const category = this.categories[i]
        for (let i2 = 0; i2 < category.templates.length; i2++) {
          const template = category.templates[i2]
          if (template.is_default) {
            this.$nextTick(() => {
              this.$refs.categories.selectCategory(category.id)
              this.selectTemplate({ template, category })
            })
            return
          }
        }
      }
    },
    selectTemplate({ template, category }) {
      this.selectedTemplate = template
      this.selectedTemplateCategory = category
    },
  },
}
</script>
