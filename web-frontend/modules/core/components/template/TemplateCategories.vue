<template>
  <div class="templates__sidebar">
    <slot></slot>
    <div class="templates__sidebar-title">Templates</div>
    <div class="templates__search">
      <div class="input__with-icon input__with-icon--left">
        <input
          v-model="search"
          type="text"
          class="input"
          placeholder="Search templates"
        />
        <i class="fas fa-search"></i>
      </div>
    </div>
    <ul class="templates__categories">
      <li
        v-for="category in matchingCategories"
        :key="category.id"
        class="templates__category"
        :class="{
          'templates__category--open': category.id === selectedCategoryId,
        }"
      >
        <a
          class="templates__category-link"
          @click="selectCategory(category.id)"
          >{{ category.name }}</a
        >
        <ul class="templates__templates">
          <li
            v-for="template in category.templates"
            :key="template.id"
            class="templates__template"
            :class="{
              'templates__template--active':
                selectedTemplate !== null && template.id == selectedTemplate.id,
            }"
          >
            <a
              class="templates__template-link"
              @click="$emit('selected', { template, category })"
            >
              <i class="fas fa-fw" :class="'fa-' + template.icon"></i>
              {{ template.name }}
            </a>
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script>
import { escapeRegExp } from '@baserow/modules/core/utils/string'
import { clone } from '@baserow/modules/core/utils/object'

export default {
  name: 'TemplateCategories',
  props: {
    categories: {
      type: Array,
      required: true,
    },
    selectedTemplate: {
      required: true,
      validator: (prop) => typeof prop === 'object' || prop === null,
    },
  },
  data() {
    return {
      search: '',
      selectedCategoryId: -1,
    }
  },
  computed: {
    /**
     * Returns the categories and templates that match the search query.
     */
    matchingCategories() {
      if (this.search === '') {
        return this.categories
      }

      return clone(this.categories)
        .map((category) => {
          category.templates = category.templates.filter((template) => {
            const keywords = template.keywords.split(',')
            keywords.push(template.name)
            const regex = new RegExp('(' + escapeRegExp(this.search) + ')', 'i')
            return keywords.some((value) => value.match(regex))
          })
          return category
        })
        .filter((category) => category.templates.length > 0)
    },
  },
  methods: {
    selectCategory(id) {
      this.selectedCategoryId = this.selectedCategoryId === id ? -1 : id
    },
  },
}
</script>
