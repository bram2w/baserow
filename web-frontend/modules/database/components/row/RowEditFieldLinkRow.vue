<template>
  <div class="control__elements">
    <ul class="field-link-row__items">
      <li v-for="item in value" :key="item.id" class="field-link-row__item">
        <component
          :is="readOnly ? 'span' : 'a'"
          class="field-link-row__name"
          :class="{
            'field-link-row__name--unnamed':
              item.value === null || item.value === '',
          }"
          @click.prevent="showForeignRowModal(item)"
        >
          {{ item.value || 'unnamed row ' + item.id }}
        </component>
        <span
          v-if="itemLoadingId === item.id"
          class="field-link-row__loading"
        ></span>
        <a
          v-else-if="!readOnly"
          class="field-link-row__remove"
          @click.prevent.stop="removeValue($event, value, item.id)"
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
      :table-id="field.link_row_table_id"
      :value="value"
      @selected="addValue(value, $event)"
    ></SelectRowModal>
    <ForeignRowEditModal
      v-if="!readOnly"
      ref="rowEditModal"
      :table-id="field.link_row_table_id"
      @hidden="modalOpen = false"
    ></ForeignRowEditModal>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import linkRowField from '@baserow/modules/database/mixins/linkRowField'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'
import ForeignRowEditModal from '@baserow/modules/database/components/row/ForeignRowEditModal'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  components: { SelectRowModal, ForeignRowEditModal },
  mixins: [rowEditField, linkRowField],
  data() {
    return {
      itemLoadingId: -1,
    }
  },
  methods: {
    removeValue(...args) {
      linkRowField.methods.removeValue.call(this, ...args)
      this.touch()
    },
    addValue(...args) {
      linkRowField.methods.addValue.call(this, ...args)
      this.touch()
    },
    async showForeignRowModal(item) {
      if (this.readOnly) {
        return
      }

      this.itemLoadingId = item.id
      try {
        await this.$refs.rowEditModal.show(item.id)
      } catch (error) {
        notifyIf(error)
      }
      this.itemLoadingId = -1
    },
  },
}
</script>
