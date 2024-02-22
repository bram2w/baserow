<template>
  <nuxt-link
    class="notification-panel__notification-link"
    :to="url"
    @click.native="markAsReadAndHandleClick"
  >
    <div class="notification-panel__notification-content-title">
      <i18n path="rowCommentNotification.title" tag="span">
        <template #sender>
          <strong v-if="sender">{{ sender }}</strong>
          <strong v-else
            ><s>{{ $t('rowCommentNotification.deletedUser') }}</s></strong
          >
        </template>
        <template #row>
          <strong>{{
            notification.data.row_name ?? notification.data.row_id
          }}</strong>
        </template>
        <template #table>
          <strong>{{ notification.data.table_name }}</strong>
        </template>
      </i18n>
    </div>
    <RichTextEditor
      :editable="false"
      :enable-mentions="true"
      :value="notification.data.message"
    />
  </nuxt-link>
</template>

<script>
import RichTextEditor from '@baserow/modules/core/components/editor/RichTextEditor.vue'
import notificationContent from '@baserow/modules/core/mixins/notificationContent'

export default {
  name: 'RowCommentNotification',
  components: {
    RichTextEditor,
  },
  mixins: [notificationContent],
  props: {
    notification: {
      type: Object,
      required: true,
    },
  },
  computed: {
    params() {
      const data = this.notification.data
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
        databaseId: data.database_id,
        tableId: data.table_id,
        rowId: data.row_id,
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
    handleClick(evt) {
      this.$emit('close-panel')
    },
  },
}
</script>
