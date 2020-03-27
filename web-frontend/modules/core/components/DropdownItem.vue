<template>
  <li class="select-item" :class="{ hidden: !isVisible(query) }">
    <a class="select-item-link" @click="select(value)">
      <i
        v-if="icon"
        class="select-item-icon fas fa-fw"
        :class="'fa-' + icon"
      ></i>
      {{ name }}
    </a>
  </li>
</template>

<script>
export default {
  name: 'DropdownItem',
  props: {
    value: {
      type: [String, Number, Boolean, Object],
      required: true
    },
    name: {
      type: String,
      required: true
    },
    icon: {
      type: String,
      required: false,
      default: null
    }
  },
  data() {
    return {
      query: ''
    }
  },
  methods: {
    select(value) {
      this.$parent.select(value)
    },
    search(query) {
      this.query = query
    },
    isVisible(query) {
      const regex = new RegExp('(' + query + ')', 'i')
      return this.name.match(regex)
    }
  }
}
</script>
