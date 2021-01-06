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
          class="field-link-row__remove"
          @click.prevent="removeValue($event, value, item.id)"
        >
          <i class="fas fa-times"></i>
        </a>
      </li>
    </ul>
    <a class="add" @click.prevent="$refs.selectModal.show()">
      <i class="fas fa-plus add__icon"></i>
      Add another link
    </a>
    <SelectRowModal
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
}
</script>
