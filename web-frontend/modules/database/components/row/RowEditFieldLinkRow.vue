<template>
  <div class="control__elements">
    <ul class="field-link-row__items">
      <li v-for="item in value" :key="item.id" class="field-link-row__item">
        <span
          class="field-link-row__name"
          :class="{
            'field-link-row__name--unnamed':
              item.value === null || item.value === '',
          }"
        >
          {{ item.value || 'unnamed row ' + item.id }}
        </span>
        <a
          v-if="!readOnly"
          class="field-link-row__remove"
          @click.prevent="removeValue($event, value, item.id)"
        >
          <i class="fas fa-times"></i>
        </a>
      </li>
    </ul>
    <a v-if="!readOnly" class="add" @click.prevent="$refs.selectModal.show()">
      <i class="fas fa-plus add__icon"></i>
      {{ $t('rowEditFieldLinkRow.addLink') }}
    </a>
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
    <SelectRowModal
      v-if="!readOnly"
      ref="selectModal"
      :table-id="field.link_row_table"
      :value="value"
      @selected="addValue(value, $event)"
    ></SelectRowModal>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import linkRowField from '@baserow/modules/database/mixins/linkRowField'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'

export default {
  components: { SelectRowModal },
  mixins: [rowEditField, linkRowField],
  methods: {
    removeValue(...args) {
      linkRowField.methods.removeValue.call(this, ...args)
      this.touch()
    },
    addValue(...args) {
      linkRowField.methods.addValue.call(this, ...args)
      this.touch()
    },
  },
}
</script>

<i18n>
{
  "en": {
    "rowEditFieldLinkRow": {
      "addLink": "Add another link"
    }
  },
  "fr": {
    "rowEditFieldLinkRow": {
      "addLink": "Ajouter un lien"
    }
  }
}
</i18n>
