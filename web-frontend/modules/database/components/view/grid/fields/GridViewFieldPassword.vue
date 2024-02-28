<template>
  <div
    ref="cell"
    class="grid-view__cell active"
    :class="{ editing: editing }"
    @contextmenu="stopContextIfEditing($event)"
  >
    <div v-if="!editing" class="grid-field-password">
      <div class="grid-field-password__dots">
        {{ value ? '••••••••••' : '' }}
      </div>
      <div class="grid-field-password__link">
        <a @click="edit()">
          {{ value ? $t('action.change') : $t('action.set') }}
        </a>
      </div>
    </div>
    <input
      v-else
      ref="input"
      v-model="copy"
      type="password"
      class="grid-field-text__input"
    />
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'

export default {
  mixins: [gridField, gridFieldInput],
  methods: {
    afterEdit() {
      this.copy = ''
      this.$nextTick(() => {
        this.$refs.input.focus()
      })
    },
  },
}
</script>
