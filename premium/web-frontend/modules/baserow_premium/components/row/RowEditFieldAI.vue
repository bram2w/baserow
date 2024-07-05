<template>
  <div class="control__elements">
    <FormTextarea
      ref="input"
      v-model="value"
      type="text"
      class="margin-bottom-2"
      :rows="6"
      :disabled="true"
    />

    <template v-if="!readOnly">
      <Button
        v-if="isDeactivated && rowIsCreated"
        type="secondary"
        icon="iconoir-lock"
        @click="$refs.clickModal.show()"
      >
        {{ $t('rowEditFieldAI.generate') }}
      </Button>
      <Button
        v-if="rowIsCreated"
        type="secondary"
        :loading="generating"
        @click="generate()"
        >{{ $t('rowEditFieldAI.generate') }}</Button
      >
      <div v-else>{{ $t('rowEditFieldAI.createRowBefore') }}</div>
      <component
        :is="deactivatedClickComponent"
        v-if="isDeactivated"
        ref="clickModal"
        :workspace="workspace"
        :name="fieldName"
      ></component>
    </template>
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
