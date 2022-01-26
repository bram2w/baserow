<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{ 'active--primary': view.public }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon fas fa-share-square"></i>
      <span class="header__filter-name">{{
        $t('shareViewLink.shareView', { viewTypeSharingLinkName })
      }}</span>
    </a>
    <Context ref="context">
      <a
        v-if="!view.public"
        class="view-sharing__create-link"
        :class="{ 'view-sharing__create-link--disabled': readOnly }"
        @click.stop="!readOnly && updateView({ public: true })"
      >
        <i class="fas fa-share-square view-sharing__create-link-icon"></i>
        {{ $t('shareViewLink.shareViewTitle', { viewTypeSharingLinkName }) }}
      </a>
      <div v-else class="view-sharing__shared-link">
        <div class="view-sharing__shared-link-title">
          {{ $t('shareViewLink.sharedViewTitle', { viewTypeSharingLinkName }) }}
        </div>
        <div class="view-sharing__shared-link-description">
          {{
            $t('shareViewLink.sharedViewDescription', {
              viewTypeSharingLinkName,
            })
          }}
        </div>
        <div class="view-sharing__shared-link-content">
          <div class="view-sharing__shared-link-box">
            {{ shareUrl }}
          </div>
          <a
            v-tooltip="$t('shareViewLink.copyURL')"
            class="view-sharing__shared-link-action"
            @click="copyShareUrlToClipboard()"
          >
            <i class="fas fa-copy"></i>
            <Copied ref="copied"></Copied>
          </a>
        </div>
        <div v-if="!readOnly" class="view-sharing__shared-link-foot">
          <a
            class="view-sharing__shared-link-disable"
            @click.stop="updateView({ public: false })"
          >
            <i class="fas fa-times"></i>
            {{ $t('shareViewLink.disableLink') }}
          </a>
          <a @click.prevent="$refs.rotateSlugModal.show()">
            <i class="fas fa-sync"></i>
            {{ $t('shareViewLink.generateNewUrl') }}
          </a>
          <ViewRotateSlugModal
            ref="rotateSlugModal"
            :view="view"
          ></ViewRotateSlugModal>
        </div>
      </div>
    </Context>
  </div>
</template>

<script>
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'
import ViewRotateSlugModal from '@baserow/modules/database/components/view/ViewRotateSlugModal'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'ShareViewLink',
  components: { ViewRotateSlugModal },
  props: {
    view: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      rotateSlugLoading: false,
    }
  },
  computed: {
    shareUrl() {
      return (
        this.$env.PUBLIC_WEB_FRONTEND_URL +
        this.$nuxt.$router.resolve({
          name: this.viewType.getPublicRoute(),
          params: { slug: this.view.slug },
        }).href
      )
    },
    viewType() {
      return this.$registry.get('view', this.view.type)
    },
    viewTypeSharingLinkName() {
      return this.viewType.getSharingLinkName()
    },
  },
  methods: {
    copyShareUrlToClipboard() {
      copyToClipboard(this.shareUrl)
      this.$refs.copied.show()
    },
    async updateView(values) {
      const view = this.view
      this.$store.dispatch('view/setItemLoading', { view, value: true })

      try {
        await this.$store.dispatch('view/update', {
          view,
          values,
        })
      } catch (error) {
        notifyIf(error, 'view')
      }

      this.$store.dispatch('view/setItemLoading', { view, value: false })
    },
  },
}
</script>
