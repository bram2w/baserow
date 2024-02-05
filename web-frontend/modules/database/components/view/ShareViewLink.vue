<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{ 'active--primary': view.public }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon iconoir-share-android"></i>
      <span class="header__filter-name">
        {{ $t('shareViewLink.shareView', { viewTypeSharingLinkName }) }}
      </span>
    </a>
    <Context
      ref="context"
      :overflow-scroll="true"
      :max-height-if-outside-viewport="true"
    >
      <a
        v-if="!view.public"
        class="view-sharing__create-link"
        :class="{ 'view-sharing__create-link--disabled': readOnly }"
        @click.stop="!readOnly && updateView({ public: true })"
      >
        <i class="iconoir-share-android view-sharing__create-link-icon"></i>
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
          <div class="view-sharing__shared-link-box">{{ shareUrl }}</div>
          <a
            v-tooltip="$t('shareViewLink.copyURL')"
            class="view-sharing__shared-link-action"
            @click="copyShareUrlToClipboard()"
          >
            <i class="iconoir-copy"></i>
            <Copied ref="copied"></Copied>
          </a>
          <a
            v-if="!readOnly"
            v-tooltip="$t('shareViewLink.generateNewUrl')"
            class="view-sharing__shared-link-action"
            @click.prevent="$refs.rotateSlugModal.show()"
          >
            <i class="iconoir-refresh-double"></i>
            <ViewRotateSlugModal
              ref="rotateSlugModal"
              :view="view"
            ></ViewRotateSlugModal>
          </a>
        </div>
        <div class="view-sharing__shared-link-options">
          <div class="view-sharing__option">
            <SwitchInput
              class="margin-bottom-1"
              small
              :value="view.public_view_has_password"
              @input="toggleShareViewPassword"
            >
              <i
                class="view-sharing__option-icon"
                :class="[
                  view.public_view_has_password
                    ? 'iconoir-lock'
                    : 'iconoir-globe',
                ]"
              ></i>
              <span>{{ $t(optionPasswordText) }}</span>
            </SwitchInput>

            <a
              v-if="view.public_view_has_password"
              class="view-sharing__option-change-password"
              @click.stop="$refs.enablePasswordModal.show"
            >
              {{ $t('shareViewLink.ChangePassword') }}
              <i class="iconoir-edit-pencil"></i>
            </a>
            <EnablePasswordModal ref="enablePasswordModal" :view="view" />
            <DisablePasswordModal ref="disablePasswordModal" :view="view" />
          </div>
          <component
            :is="component"
            v-for="(component, i) in additionalShareLinkOptions"
            :key="i"
            :view="view"
            @update-view="forceUpdateView"
          />
        </div>
        <div v-if="!readOnly" class="view-sharing__shared-link-foot">
          <a
            class="view-sharing__shared-link-disable"
            @click.stop="updateView({ public: false })"
          >
            <i class="iconoir-cancel"></i>
            {{ $t('shareViewLink.disableLink') }}
          </a>
        </div>
      </div>
    </Context>
  </div>
</template>

<script>
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'
import ViewRotateSlugModal from '@baserow/modules/database/components/view/ViewRotateSlugModal'
import EnablePasswordModal from '@baserow/modules/database/components/view/public/EnablePasswordModal'
import DisablePasswordModal from '@baserow/modules/database/components/view/public/DisablePasswordModal'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'ShareViewLink',
  components: {
    ViewRotateSlugModal,
    EnablePasswordModal,
    DisablePasswordModal,
  },
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
        this.$config.BASEROW_EMBEDDED_SHARE_URL +
        this.$router.resolve({
          name: this.viewType.getPublicRoute(),
          params: { slug: this.view.slug },
        }).href
      )
    },
    optionPasswordText() {
      return this.view.public_view_has_password
        ? 'shareViewLink.DisablePassword'
        : 'shareViewLink.EnablePassword'
    },
    viewType() {
      return this.$registry.get('view', this.view.type)
    },
    viewTypeSharingLinkName() {
      return this.viewType.getSharingLinkName()
    },
    additionalShareLinkOptions() {
      return Object.values(this.$registry.getAll('plugin'))
        .reduce((components, plugin) => {
          components = components.concat(plugin.getAdditionalShareLinkOptions())
          return components
        }, [])
        .filter((component) => component !== null)
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
    forceUpdateView(values) {
      this.$store.dispatch('view/forceUpdate', {
        view: this.view,
        values,
      })
    },
    toggleShareViewPassword() {
      if (this.view.public_view_has_password) {
        this.$refs.disablePasswordModal.show()
      } else {
        this.$refs.enablePasswordModal.show()
      }
    },
  },
}
</script>
