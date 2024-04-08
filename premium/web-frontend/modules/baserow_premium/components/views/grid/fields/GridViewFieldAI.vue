<template>
  <div>
    <div
      v-if="(!value || (!opened && generating)) && !readOnly"
      ref="cell"
      class="grid-view__cell active"
    >
      <div class="grid-field-button">
        <button
          class="button button--tiny button--ghost"
          :disabled="!modelAvailable || generating"
          :class="{ 'button--loading': generating }"
          @click="generate()"
        >
          {{ $t('gridViewFieldAI.generate') }}
          <i v-if="isDeactivated" class="iconoir-lock"></i>
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
          <template v-if="!readOnly">
            <button
              v-if="!isDeactivated"
              class="button button--link"
              :disabled="!modelAvailable || generating"
              :class="{ 'button--loading': generating }"
              @click.prevent.stop="generate()"
            >
              <i class="button__icon iconoir-magic-wand"></i>
              {{ $t('gridViewFieldAI.regenerate') }}
            </button>
            <button
              v-else
              class="button button--link"
              @click.prevent.stop="$refs.clickModal.show()"
            >
              <i class="button__icon iconoir-lock"></i>
              {{ $t('gridViewFieldAI.regenerate') }}
            </button>
          </template>
        </div>
      </template>
    </div>
    <component
      :is="deactivatedClickComponent"
      v-if="isDeactivated"
      ref="clickModal"
      :workspace="workspace"
      :name="fieldName"
    ></component>
  </div>
</template>

<script>
import { isElement } from '@baserow/modules/core/utils/dom'
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'
import gridFieldAI from '@baserow_premium/mixins/gridFieldAI'

export default {
  name: 'GridViewFieldAI',
  mixins: [gridField, gridFieldInput, gridFieldAI],
  computed: {
    fieldName() {
      return this.$registry.get('field', this.field.type).getName()
    },
  },
  methods: {
    save() {
      this.opened = false
      this.editing = false
      this.afterSave()
    },
    canUnselectByClickingOutside(event) {
      if (this.isDeactivated) {
        return !isElement(this.$refs.clickModal.$el, event.target)
      }
      return true
    },
  },
}
</script>
