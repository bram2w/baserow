<template>
  <ul v-if="!tableLoading" class="header__filter header__filter--full-width">
    <li class="header__filter-item">
      <a
        ref="contextLink"
        class="header__filter-link"
        :class="{ 'active--warning': view.public }"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
      >
        <i class="header__filter-icon fas fa-share-square"></i>
        <span class="header__filter-name">Share form</span>
      </a>
      <Context ref="context" class="view-form__shared-link-context">
        <a
          v-if="!view.public"
          class="view-form__create-link"
          :class="{ 'view-form__create-link--disabled': readOnly }"
          @click.stop="!readOnly && updateForm({ public: true })"
        >
          <i class="fas fa-share-square view-form__create-link-icon"></i>
          Create a private shareable link to the form
        </a>
        <div v-else class="view-form__shared-link">
          <div class="view-form__shared-link-title">
            This form is currently shared via a private link
          </div>
          <div class="view-form__shared-link-description">
            People who have the link can see the form in an empty state.
          </div>
          <div class="view-form__shared-link-content">
            <div class="view-form__shared-link-box">
              {{ formUrl }}
            </div>
            <a
              v-tooltip="'Copy URL'"
              class="view-form__shared-link-action"
              @click="copyFormUrlToClipboard()"
            >
              <i class="fas fa-copy"></i>
              <Copied ref="copied"></Copied>
            </a>
          </div>
          <div v-if="!readOnly" class="view-form__shared-link-foot">
            <a
              class="view-form__shared-link-disable"
              @click.stop="updateForm({ public: false })"
            >
              <i class="fas fa-times"></i>
              disable shared link
            </a>
            <a @click.prevent="$refs.rotateSlugModal.show()">
              <i class="fas fa-sync"></i>
              generate new url
            </a>
            <FormViewRotateSlugModal
              ref="rotateSlugModal"
              :view="view"
              :store-prefix="storePrefix"
            ></FormViewRotateSlugModal>
          </div>
        </div>
      </Context>
    </li>
    <li class="header__filter-item">
      <a
        :href="formUrl"
        target="_blank"
        rel="noopener"
        class="header__filter-link"
      >
        <i class="header__filter-icon fas fa-eye"></i>
        <span class="header__filter-name">Preview</span>
      </a>
    </li>
  </ul>
</template>

<script>
import { mapState } from 'vuex'

import formViewHelpers from '@baserow/modules/database/mixins/formViewHelpers'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'
import FormViewRotateSlugModal from '@baserow/modules/database/components/view/form/FormViewRotateSlugModal'

export default {
  name: 'FormViewHeader',
  components: { FormViewRotateSlugModal },
  mixins: [formViewHelpers],
  props: {
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
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
    formUrl() {
      return (
        this.$env.PUBLIC_WEB_FRONTEND_URL +
        this.$nuxt.$router.resolve({
          name: 'database-table-form',
          params: { slug: this.view.slug },
        }).href
      )
    },
    ...mapState({
      tableLoading: (state) => state.table.loading,
    }),
  },
  methods: {
    copyFormUrlToClipboard() {
      copyToClipboard(this.formUrl)
      this.$refs.copied.show()
    },
  },
}
</script>
