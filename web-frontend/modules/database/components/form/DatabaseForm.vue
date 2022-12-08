<template>
  <form @submit.prevent="submit">
    <FormElement class="control">
      <label class="control__label">
        {{ $t('databaseForm.importLabel') }}
      </label>
      <div class="control__elements">
        <ul class="choice-items">
          <li>
            <a
              class="choice-items__link"
              :class="{ active: importType === 'none' }"
              @click="importType = 'none'"
            >
              <i class="choice-items__icon fas fa-clone"></i>
              {{ $t('databaseForm.emptyLabel') }}
            </a>
          </li>
          <li>
            <a
              class="choice-items__link"
              :class="{ active: importType === 'airtable' }"
              @click="importType = 'airtable'"
            >
              <i class="choice-items__icon fas fa-clone"></i>
              {{ $t('databaseForm.airtableLabel') }}
            </a>
          </li>
        </ul>
      </div>
    </FormElement>
    <template v-if="importType !== 'airtable'">
      <FormElement :error="fieldHasErrors('name')" class="control">
        <label class="control__label">
          <i class="fas fa-font"></i>
          {{ $t('applicationForm.nameLabel') }}
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
        <slot></slot>
      </FormElement>
    </template>
    <ImportFromAirtable
      v-else
      @hidden="$emit('hidden', $event)"
    ></ImportFromAirtable>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { required } from 'vuelidate/lib/validators'
import ImportFromAirtable from '@baserow/modules/database/components/airtable/ImportFromAirtable'

export default {
  name: 'DatabaseForm',
  components: { ImportFromAirtable },
  mixins: [form],
  props: {
    defaultName: {
      type: String,
      required: false,
      default: '',
    },
  },
  data() {
    return {
      values: {
        name: this.defaultName,
      },
      importType: 'none',
    }
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
