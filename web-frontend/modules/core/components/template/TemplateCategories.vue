<template>
  <div class="templates__sidebar">
    <slot></slot>
    <div class="templates__sidebar-title">
      {{ $t('templateCategories.title') }}
    </div>
    <div class="templates__search">
      <div class="input__with-icon input__with-icon--left">
        <input
          ref="searchInput"
          v-model="search"
          type="text"
          class="input"
          :placeholder="$t('templateCategories.search')"
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
import templateCategories from '@baserow/modules/core/mixins/templateCategories'

export default {
  name: 'TemplateCategories',
  mixins: [templateCategories],
  props: {
    selectedTemplate: {
      required: true,
      validator: (prop) => typeof prop === 'object' || prop === null,
    },
  },
  mounted() {
    this.$priorityBus.$on(
      'start-search',
      this.$priorityBus.level.HIGH,
      this.searchStarted
    )
  },
  beforeDestroy() {
    this.$priorityBus.$off('start-search', this.searchStarted)
  },
  methods: {
    searchStarted() {
      this.$refs.searchInput.focus()
    },
  },
}
</script>
