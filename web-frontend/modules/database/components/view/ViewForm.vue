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
          v-for="type in availableViewOwnershipTypesForCreation"
          :key="type.getType()"
          :view-ownership-type="type"
          :database="database"
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
    table: {
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
      return Object.values(this.$registry.getAll('viewOwnershipType'))
    },
    availableViewOwnershipTypesForCreation() {
      return this.activeViewOwnershipTypes.filter((t) =>
        t.userCanTryCreate(this.table, this.database.workspace.id)
      )
    },
    activeViewOwnershipTypes() {
      return this.viewOwnershipTypes
        .filter((t) => !t.isDeactivated(this.database.workspace.id))
        .sort((a, b) => b.getListViewTypeSort() - a.getListViewTypeSort())
    },
  },
  mounted() {
    this.$refs.name.focus()
    const firstAndHenceDefaultOwnershipType =
      this.availableViewOwnershipTypesForCreation[0]?.getType()
    this.values.ownershipType =
      this.defaultValues.ownershipType || firstAndHenceDefaultOwnershipType
  },
  validations: {
    values: {
      name: { required },
    },
  },
}
</script>
