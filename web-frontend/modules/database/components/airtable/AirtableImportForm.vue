<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">
        {{ $t('importFromAirtable.airtableShareLinkTitle') }}
      </label>
      <p class="margin-bottom-2">
        {{ $t('importFromAirtable.airtableShareLinkDescription') }}
        <br /><br />
        {{ $t('importFromAirtable.airtableShareLinkBeta') }}
      </p>
      <div class="control__elements">
        <input
          v-model="values.airtableUrl"
          :class="{ 'input--error': $v.values.airtableUrl.$error }"
          type="text"
          class="input"
          :placeholder="$t('importFromAirtable.airtableShareLinkPaste')"
          @blur="$v.values.airtableUrl.$touch()"
          @input="
            $emit(
              'input',
              $v.values.airtableUrl.$invalid ? '' : values.airtableUrl
            )
          "
        />
        <div v-if="$v.values.airtableUrl.$error" class="error">
          {{ $t('importFromAirtable.linkError') }}
        </div>
      </div>
    </div>
    <slot></slot>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'AirtableImportForm',
  mixins: [form],
  data() {
    return {
      values: {
        airtableUrl: '',
      },
    }
  },
  validations: {
    values: {
      airtableUrl: {
        valid(value) {
          const regex = /https:\/\/airtable.com\/[shr|app](.*)$/g
          return !!value.match(regex)
        },
      },
    },
  },
}
</script>
