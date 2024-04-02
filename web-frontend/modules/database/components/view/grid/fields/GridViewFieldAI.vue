<template>
  <div
    v-if="!value || (!opened && generating)"
    ref="cell"
    class="grid-view__cell active"
  >
    <div class="grid-field-button">
      <button
        class="button button--tiny button--ghost"
        :disabled="!modelAvailable"
        :class="{ 'button--loading': generating }"
        @click="generate()"
      >
        {{ $t('gridViewFieldAI.generate') }}
      </button>
    </div>
  </div>
  <div
    v-else
    ref="cell"
    class="grid-view__cell grid-field-long-text__cell active"
    :class="{ editing: opened }"
    @keyup.enter="opened = true"
  >
    <div v-if="!opened" class="grid-field-long-text">{{ value }}</div>
    <template v-else>
      <div class="grid-field-long-text__textarea">
        {{ value }}
      </div>
      <div style="background-color: #fff; padding: 8px">
        <button
          class="button button--link"
          :disabled="!modelAvailable"
          :class="{ 'button--loading': generating }"
          @click.prevent.stop="generate()"
        >
          <i class="button__icon iconoir-magic-wand"></i>
          {{ $t('gridViewFieldAI.regenerate') }}
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'
import gridFieldAI from '@baserow/modules/database/mixins/gridFieldAI'

export default {
  mixins: [gridField, gridFieldInput, gridFieldAI],
  methods: {
    save() {
      this.opened = false
      this.editing = false
      this.afterSave()
    },
  },
}
</script>
