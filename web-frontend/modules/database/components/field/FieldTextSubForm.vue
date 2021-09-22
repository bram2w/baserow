<template>
  <div>
    <div class="control">
      <div class="control__elements">
        <input
          ref="text_default"
          v-model="values.text_default"
          type="text"
          class="input"
          :placeholder="$t('fieldTextSubForm.placeholder')"
        />
      </div>
    </div>
  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FieldTextSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['text_default'],
      values: {
        text_default: '',
      },
    }
  },
  methods: {
    isFormValid() {
      return true
    },
  },
}
</script>

<i18n>
{
  "en": {
    "fieldTextSubForm": {
      "placeholder": "Default text"
    }
  },
  "fr": {
    "fieldTextSubForm": {
      "placeholder": "Texte par défault"
    }
  }
}
</i18n>
