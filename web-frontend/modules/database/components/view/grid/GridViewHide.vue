<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{
        'active--error': hiddenFields.length > 0,
      }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon fas fa-eye-slash"></i>
      <span class="header__filter-name">{{
        $tc('gridViewHide.hideField', hiddenFields.length, {
          count: hiddenFields.length,
        })
      }}</span>
    </a>
    <GridViewHideContext
      ref="context"
      :view="view"
      :fields="fields"
      :read-only="readOnly"
      :store-prefix="storePrefix"
    ></GridViewHideContext>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import GridViewHideContext from '@baserow/modules/database/components/view/grid/GridViewHideContext'

export default {
  name: 'GridViewHide',
  components: { GridViewHideContext },
  props: {
    fields: {
      type: Array,
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
    hiddenFields() {
      return this.fields.filter((field) => {
        const exists = Object.prototype.hasOwnProperty.call(
          this.fieldOptions,
          field.id
        )
        return !exists || (exists && this.fieldOptions[field.id].hidden)
      })
    },
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        fieldOptions:
          this.$options.propsData.storePrefix + 'view/grid/getAllFieldOptions',
      }),
    }
  },
}
</script>

<i18n>
{
  "en":{
    "gridViewHide": {
      "hideField": "Hide Fields | 1 hidden field | {count} hidden fields"
    }
  },
  "fr":{
    "gridViewHide": {
      "hideField": "Cacher des colonnes | 1 colonne cachée | {count} colonnes cachées"
    }
  }
}
</i18n>
