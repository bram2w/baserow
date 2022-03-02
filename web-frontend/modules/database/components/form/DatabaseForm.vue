<template>
  <form @submit.prevent="submit">
    <div class="control">
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
    </div>
    <template v-if="importType !== 'airtable'">
      <div class="control">
        <label class="control__label">
          <i class="fas fa-font"></i>
          {{ $t('applicationForm.nameLabel') }}
        </label>
        <div class="control__elements">
          <input
            ref="name"
            v-model="values.name"
            :class="{ 'input--error': $v.values.name.$error }"
            type="text"
            class="input input--large"
            @blur="$v.values.name.$touch()"
          />
          <div v-if="$v.values.name.$error" class="error">
            {{ $t('error.requiredField') }}
          </div>
        </div>
        <slot></slot>
      </div>
    </template>
    <ImportFromAirtable
      v-else
      @hidden="$emit('hidden', $event)"
    ></ImportFromAirtable>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import ImportFromAirtable from '@baserow/modules/database/components/airtable/ImportFromAirtable'

export default {
  name: 'DatabaseForm',
  components: { ImportFromAirtable },
  mixins: [form],
  data() {
    return {
      values: {
        name: '',
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
