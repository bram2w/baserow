<template>
  <div>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldSingleSelectSubForm.optionsLabel')
      }}</label>
      <div class="control__elements">
        <FieldSelectOptions
          ref="selectOptions"
          v-model="values.select_options"
        ></FieldSelectOptions>
      </div>
    </div>
  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import FieldSelectOptions from '@baserow/modules/database/components/field/FieldSelectOptions'

export default {
  name: 'FieldNumberSubForm',
  components: { FieldSelectOptions },
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['select_options'],
      values: {
        select_options: [],
      },
    }
  },
  methods: {
    isFormValid() {
      this.$refs.selectOptions.$v.$touch()
      return !this.$refs.selectOptions.$v.$invalid
    },
  },
}
</script>

<i18n>
{
  "en": {
    "fieldSingleSelectSubForm": {
      "optionsLabel": "Options"
    }
  },
  "fr": {
    "fieldSingleSelectSubForm": {
      "optionsLabel": "Options"
    }
  }
}
</i18n>
