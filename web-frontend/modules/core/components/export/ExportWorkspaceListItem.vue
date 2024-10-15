<template>
  <div class="exports-modal__export">
    <div class="exports-modal__info">
      <div>
        <div class="exports-modal__name">
          {{ name }}
        </div>
        <div class="exports-modal__detail">
          {{ $t('snapshotListItem.created') }} {{ timeAgo }}
        </div>
      </div>
    </div>
    <div class="exports-modal__actions">
      <DownloadLink
        :url="exportJob.url"
        :filename="exportJob.exported_file_name"
        :loading-class="'button--loading'"
      >
        {{ $t('exportWorkspaceModal.download') }}
      </DownloadLink>
    </div>
  </div>
</template>

<script>
import timeAgo from '@baserow/modules/core/mixins/timeAgo'
import moment from '@baserow/modules/core/moment'

export default {
  mixins: [timeAgo],
  props: {
    exportJob: {
      type: Object,
      required: true,
    },
    workspace: {
      type: Object,
      required: true,
    },
  },
  computed: {
    name() {
      return `${this.workspace.name} - ${moment(
        this.exportJob.created_on
      ).format('YYYY-MM-DD HH:mm:ss')}`
    },
  },
}
</script>
