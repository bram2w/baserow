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
}
</script>
