<template>
  <div>
    <form v-if="dateFields.length > 0" @submit.prevent="submit">
      <FormElement class="control">
        <label class="control__label">
          {{ $t('dateFieldSelectForm.dateField') }}
        </label>
        <div class="control__elements">
          <Dropdown v-model="values.dateFieldId" :show-search="true">
            <DropdownItem
              v-for="dateField in dateFields"
              :key="dateField.id"
              :name="dateField.name"
              :value="dateField.id"
              :icon="fieldIcon(dateField.type)"
            >
            </DropdownItem>
          </Dropdown>
          <div v-if="fieldHasErrors('dateFieldId')" class="error">
            {{ $t('error.requiredField') }}
          </div>
        </div>
      </FormElement>
      <slot></slot>
    </form>
    <div v-else class="warning">
      {{ $t('dateFieldSelectForm.noCompatibleDateFields') }}
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'DateFieldSelectForm',
  mixins: [form],
  props: {
    table: {
      type: Object,
      required: true,
    },
    dateFields: {
      type: Array,
      required: true,
    },
    dateFieldId: {
      type: Number,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      values: {
        dateFieldId: null,
      },
    }
  },
  mounted() {
    this.values.dateFieldId =
      this.dateFieldId || (this.dateFields.length > 0 && this.dateFields[0]?.id)
  },
  methods: {
    fieldIcon(type) {
      const ft = this.$registry.get('field', type)
      return ft?.getIconClass() || 'calendar-alt'
    },
  },
  validations: {
    values: {
      dateFieldId: { required },
    },
  },
}
</script>
