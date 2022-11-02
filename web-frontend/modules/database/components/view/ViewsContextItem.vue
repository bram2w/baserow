<template>
  <li
    v-tooltip="deactivated ? deactivatedText : null"
    class="select__item"
    :class="{
      active: view._.selected,
      'select__item--loading': view._.loading,
      'select__item--no-options': readOnly,
    }"
  >
    <a class="select__item-link" @click="select(view)">
      <div class="select__item-name">
        <i
          class="select__item-icon fas fa-fw"
          :class="view._.type.colorClass + ' fa-' + view._.type.iconClass"
        ></i>
        <EditableViewName ref="rename" :view="view"></EditableViewName>
        <div v-if="deactivated" class="deactivated-label">
          <i class="fas fa-lock"></i>
        </div>
      </div>
    </a>
    <component
      :is="deactivatedClickModal"
      v-if="deactivatedClickModal !== null"
      ref="deactivatedClickModal"
      :name="viewType.getName()"
    ></component>
    <template v-if="!readOnly && showViewContext">
      <a
        ref="contextLink"
        class="select__item-options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
        @mousedown.stop
      >
        <i class="fas fa-ellipsis-v"></i>
      </a>
      <ViewContext
        ref="context"
        :database="database"
        :table="table"
        :view="view"
        @enable-rename="enableRename"
      ></ViewContext>
    </template>
  </li>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import ViewContext from '@baserow/modules/database/components/view/ViewContext'
import EditableViewName from '@baserow/modules/database/components/view/EditableViewName'

export default {
  name: 'ViewsContextItem',
  components: { EditableViewName, ViewContext },
  mixins: [context],
  props: {
    database: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  computed: {
    viewType() {
      return this.$registry.get('view', this.view.type)
    },
    deactivatedText() {
      return this.viewType.getDeactivatedText({ view: this.view })
    },
    deactivated() {
      return (
        !this.readOnly && this.viewType.isDeactivated(this.database.group.id)
      )
    },
    deactivatedClickModal() {
      return this.deactivated ? this.viewType.getDeactivatedClickModal() : null
    },
    showViewContext() {
      return (
        this.$hasPermission(
          'database.table.run_export',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.import_rows',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.duplicate',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.create_webhook',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.update',
          this.view,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.delete',
          this.view,
          this.database.group.id
        )
      )
    },
  },
  methods: {
    enableRename() {
      this.$refs.rename.edit()
    },
    select(view) {
      if (this.deactivated) {
        this.$refs.deactivatedClickModal.show()
        return
      }
      this.$emit('selected', view)
    },
  },
}
</script>
