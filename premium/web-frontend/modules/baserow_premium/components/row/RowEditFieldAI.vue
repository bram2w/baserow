<template>
  <div class="control__elements">
    <textarea
      ref="input"
      v-model="value"
      type="text"
      class="input field-long-text margin-bottom-2"
      :disabled="true"
    />
    <a
      v-if="isDeactivated && rowIsCreated"
      class="button button--ghost"
      @click="$refs.clickModal.show()"
    >
      <i class="iconoir-lock"></i>
      {{ $t('rowEditFieldAI.generate') }}
    </a>
    <a
      v-else-if="rowIsCreated"
      class="button button--ghost"
      :class="{ 'button--loading': generating }"
      @click="generate()"
      >{{ $t('rowEditFieldAI.generate') }}</a
    >
    <div v-else>{{ $t('rowEditFieldAI.createRowBefore') }}</div>
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
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import fieldAI from '@baserow_premium/mixins/fieldAI'

export default {
  name: 'RowEditFieldAI',
  mixins: [rowEditField, fieldAI],
  computed: {
    fieldName() {
      return this.$registry.get('field', this.field.type).getName()
    },
  },
}
</script>
