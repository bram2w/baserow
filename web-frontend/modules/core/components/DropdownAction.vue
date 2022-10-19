<template>
  <li class="dropdown__action" @click="$emit('click')">
    <a class="dropdown__action__link" :class="colorClass">{{ label }}</a>
  </li>
</template>

<script>
export default {
  name: 'DropdownAction',
  props: {
    label: {
      required: true,
      type: String,
    },
    colorClass: {
      required: false,
      type: String,
      default: () => 'color--deep-dark-gray',
    },
  },
}
</script>
