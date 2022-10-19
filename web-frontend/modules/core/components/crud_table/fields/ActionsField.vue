<template>
  <div>
    <a ref="contextLink" class="crudtable__actions-field__link" @click="show">
      <i class="fas fa-ellipsis-h"></i>
    </a>
    <Context ref="context">
      <ul class="context__menu">
        <li
          v-for="action in enabledActions"
          :key="action.label"
          @click="$emit(action.onClickEventName, row)"
        >
          <a :class="action.colorClass || 'color--deep-dark-gray'">
            {{ action.label }}
          </a>
        </li>
      </ul>
    </Context>
  </div>
</template>

<script>
export default {
  name: 'ActionsField',
  props: {
    row: {
      required: true,
      type: Object,
    },
    column: {
      required: true,
      type: Object,
    },
  },
  computed: {
    enabledActions() {
      return this.column.additionalProps.actions.filter(
        (action) => !this.disabled(action.disabled)
      )
    },
  },
  methods: {
    show() {
      this.$refs?.context?.toggle(this.$refs.contextLink, 'bottom', 'right')
    },
    disabled(disabledProp) {
      if (typeof disabledProp === 'function') {
        return disabledProp(this.row)
      } else {
        return disabledProp || false
      }
    },
  },
}
</script>
