<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{
        'active--primary': hiddenFields.length > 0,
      }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon fas fa-eye-slash"></i>
      {{ hiddenFieldsTitle }}
    </a>
    <GridViewHideContext
      ref="context"
      :view="view"
      :fields="fields"
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
    hiddenFieldsTitle() {
      const numberOfHiddenFields = this.hiddenFields.length
      if (numberOfHiddenFields === 0) {
        return 'Hide Fields'
      } else if (numberOfHiddenFields === 1) {
        return `${numberOfHiddenFields} hidden field`
      } else {
        return `${numberOfHiddenFields} hidden fields`
      }
    },
    ...mapGetters({
      fieldOptions: 'view/grid/getAllFieldOptions',
    }),
  },
}
</script>
