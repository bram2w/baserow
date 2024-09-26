<template>
  <div>
    <a
      ref="dropdownLink"
      class="header__filter-link"
      @click="$refs.dropdown.toggle($refs.dropdownLink)"
    >
      <i class="header__filter-icon iconoir-table-rows"></i>
      <span class="header__filter-name">{{
        $t('gridViewRowHeight.name')
      }}</span>
    </a>
    <Dropdown
      ref="dropdown"
      :show-search="false"
      :show-input="false"
      :value="view.row_height_size"
      @input="setSize"
    >
      <DropdownItem
        :name="$t('gridViewRowHeight.small')"
        value="small"
        :disabled="readOnly && !isPublic"
      ></DropdownItem>
      <DropdownItem
        :name="$t('gridViewRowHeight.medium')"
        value="medium"
        :disabled="readOnly && !isPublic"
      ></DropdownItem>
      <DropdownItem
        :name="$t('gridViewRowHeight.large')"
        value="large"
        :disabled="readOnly && !isPublic"
      ></DropdownItem>
    </Dropdown>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'GridViewRowHeight',
  props: {
    database: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      isPublic: 'page/view/public/getIsPublic',
    }),
  },
  methods: {
    async setSize(value) {
      try {
        await this.$store.dispatch('view/update', {
          view: this.view,
          values: { row_height_size: value },
          readOnly:
            this.readOnly ||
            !this.$hasPermission(
              'database.table.view.update',
              this.view,
              this.database.workspace.id
            ),
        })
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
  },
}
</script>
