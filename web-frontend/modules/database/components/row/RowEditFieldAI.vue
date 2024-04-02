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
      v-if="rowIsCreated"
      class="button button--ghost"
      :class="{ 'button--loading': generating }"
      @click="generate()"
      >{{ $t('rowEditFieldAI.generate') }}</a
    >
    <div v-else>{{ $t('rowEditFieldAI.createRowBefore') }}</div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import fieldAI from '@baserow/modules/database/mixins/fieldAI'

export default {
  mixins: [rowEditField, fieldAI],
}
</script>
