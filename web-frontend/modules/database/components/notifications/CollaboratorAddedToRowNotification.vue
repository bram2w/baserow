<template>
  <nuxt-link
    class="notification-panel__notification-link"
    :to="url"
    @click.native="markAsReadAndHandleClick"
  >
    <div class="notification-panel__notification-content-title">
      <i18n path="collaboratorAddedToRowNotification.title" tag="span">
        <template #sender>
          <strong>{{
            notification.sender?.first_name || $t('anonymous')
          }}</strong>
        </template>
        <template #fieldName>
          <strong>{{ notification.data.field_name }}</strong>
        </template>
        <template #rowId>
          <strong>{{ notification.data.row_id }}</strong>
        </template>
        <template #tableName>
          <strong>{{ notification.data.table_name }}</strong>
        </template>
      </i18n>
    </div>
  </nuxt-link>
</template>

<script>
import notificationContent from '@baserow/modules/core/mixins/notificationContent'

export default {
  name: 'CollaboratorAddedToRowNotification',
  mixins: [notificationContent],
  props: {
    notification: {
      type: Object,
      required: true,
    },
  },
  computed: {
    params() {
      let viewId = null

      if (
        ['database-table-row', 'database-table'].includes(
          this.$nuxt.$route.name
        ) &&
        this.$nuxt.$route.params.tableId === this.notification.data.table_id
      ) {
        viewId = this.$nuxt.$route.params.viewId
      }

      return {
        databaseId: this.notification.data.database_id,
        tableId: this.notification.data.table_id,
        rowId: this.notification.data.row_id,
        viewId,
      }
    },
    url() {
      return {
        name: 'database-table-row',
        params: this.params,
      }
    },
  },
  methods: {
    handleClick() {
      this.$emit('close-panel')
    },
  },
}
</script>
