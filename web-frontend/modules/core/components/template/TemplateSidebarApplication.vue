<template>
  <li
    class="tree__item"
    :class="{
      active: application._.selected,
      'tree__item--loading': application._.loading,
    }"
  >
    <div class="tree__action">
      <a class="tree__link">
        <i
          class="tree__icon tree__icon--type fas"
          :class="'fa-' + application._.type.iconClass"
        ></i>
        {{ application.name }}
      </a>
    </div>
    <template
      v-if="
        application._.selected && application._.type.hasSelectedSidebarComponent
      "
    >
      <component
        :is="selectedApplicationComponent"
        :application="application"
      ></component>
    </template>
  </li>
</template>

<script>
export default {
  name: 'TemplatesSidebarApplication',
}
</script>
