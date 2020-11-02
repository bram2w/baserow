<template>
  <li>
    <nuxt-link
      :to="{
        name: 'database-api-docs-detail',
        params: {
          databaseId: application.id,
        },
      }"
    >
      <i class="context__menu-icon fas fa-fw fa-book"></i>
      View API docs
    </nuxt-link>
  </li>
</template>

<script>
export default {
  name: 'Context',
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
}
</script>
