<template>
  <li
    class="tree__item"
    :class="{
      active: application._.selected,
      'tree__item--loading': application._.loading,
    }"
  >
    <div class="tree__action">
      <a class="tree__link" @click="$emit('selected', application)">
        <i
          class="tree__icon tree__icon--type fas"
          :class="'fa-' + application._.type.iconClass"
        ></i>
        {{ application.name }}
      </a>
    </div>
    <template v-if="application._.selected">
      <ul class="tree__subs">
        <li
          v-for="table in orderedTables"
          :key="table.id"
          class="tree__sub"
          :class="{ active: isTableActive(table) }"
        >
          <a class="tree__sub-link" @click="selectTable(application, table)">
            {{ table.name }}
          </a>
        </li>
      </ul>
    </template>
  </li>
</template>

<script>
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'

export default {
  name: 'TemplateSidebar',
  props: {
    application: {
      type: Object,
      required: true,
    },
    page: {
      required: true,
      validator: (prop) => typeof prop === 'object' || prop === null,
    },
  },
  computed: {
    orderedTables() {
      return this.application.tables
        .map((table) => table)
        .sort((a, b) => a.order - b.order)
    },
  },
  methods: {
    selectTable(application, table) {
      this.$emit('selected-page', {
        application: DatabaseApplicationType.getType(),
        value: {
          database: application,
          table,
        },
      })
    },
    isTableActive(table) {
      return (
        this.page !== null &&
        this.page.application === DatabaseApplicationType.getType() &&
        this.page.value.table.id === table.id
      )
    },
  },
}
</script>
