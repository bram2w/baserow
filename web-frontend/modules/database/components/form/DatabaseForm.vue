<template>
  <div>
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
    <BlankDatabaseForm
      v-if="importType === 'none'"
      :default-name="defaultName"
      :loading="loading"
      @submitted="$emit('submitted', $event)"
    />
    <ImportFromAirtable
      v-else-if="importType === 'airtable'"
      @hidden="$emit('hidden', $event)"
    ></ImportFromAirtable>
  </div>
</template>

<script>
import ImportFromAirtable from '@baserow/modules/database/components/airtable/ImportFromAirtable'
import BlankDatabaseForm from '@baserow/modules/database/components/form/BlankDatabaseForm'

export default {
  name: 'DatabaseForm',
  components: { BlankDatabaseForm, ImportFromAirtable },
  props: {
    defaultName: {
      type: String,
      required: false,
      default: '',
    },
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      importType: 'none',
    }
  },
}
</script>
