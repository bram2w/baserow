<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <label class="control__label">
        {{ $t('viewForm.name') }}
      </label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': fieldHasErrors('name') }"
          type="text"
          class="input input--large"
          @focus.once="$event.target.select()"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="fieldHasErrors('name')" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('viewForm.whoCanEdit') }}
      </label>
      <div class="control__elements view-ownership-select">
        <component
          :is="type.getRadioComponent()"
          v-for="type in viewOwnershipTypes"
          :key="type.getType()"
          :view-ownership-type="type"
          :selected-type="values.ownershipType"
          @input="(value) => (values.ownershipType = value)"
        ></component>
      </div>
    </FormElement>
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'
import Radio from '@baserow/modules/core/components/Radio'

export default {
  name: 'ViewForm',
  components: { Radio },
  mixins: [form],
  props: {
    defaultName: {
      type: String,
      required: false,
      default: '',
    },
    database: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      values: {
        name: this.defaultName,
        ownershipType: 'collaborative',
      },
    }
  },
  computed: {
    viewOwnershipTypes() {
      return this.$registry.getAll('viewOwnershipType')
    },
  },
  mounted() {
    this.$refs.name.focus()
  },
  validations: {
    values: {
      name: { required },
    },
  },
}
</script>
