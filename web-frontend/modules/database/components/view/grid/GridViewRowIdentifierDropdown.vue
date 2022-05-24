<template>
  <div>
    <a
      ref="contextAnchor"
      class="grid-view__head-row-identifier-dropdown"
      @click.prevent="toggle"
    >
      <i class="fas fa-list-ol"></i>
    </a>

    <Context ref="context">
      <ul v-auto-overflow-scroll class="select__items">
        <li
          v-for="option in options"
          :key="option"
          class="select__item select__item-no-options"
          :class="{ active: option === rowIndetifierTypeSelected }"
        >
          <a class="select__item-link" @click="setRowIdentifierTypes(option)">
            <span class="select__item-name">
              {{ $t(`gridViewIdentifierOptions.${option}`) }}
            </span>
          </a>
        </li>
      </ul>
    </Context>
  </div>
</template>

<script>
export default {
  name: 'GridViewRowIdentifierDropdown',
  props: {
    rowIndetifierTypeSelected: {
      type: String,
      required: true,
    },
  },
  computed: {
    options() {
      return ['id', 'count']
    },
  },
  methods: {
    toggle() {
      this.$refs.context.toggle(
        this.$refs.contextAnchor,
        'bottom',
        'left',
        10,
        4
      )
    },
    setRowIdentifierTypes(rowIdentifierType) {
      this.$refs.context.hide()
      this.$emit('change', rowIdentifierType)
    },
  },
}
</script>
