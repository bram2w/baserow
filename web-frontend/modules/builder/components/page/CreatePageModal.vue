<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('createPageModal.header') }}
    </h2>
    <PageForm :creation="true" :builder="builder" @submitted="addPage">
      <FormElement>
        <div class="actions actions--right">
          <button
            :class="{ 'button--loading': loading }"
            class="button button--large"
            type="submit"
          >
            {{ $t('createPageModal.submit') }}
          </button>
        </div>
      </FormElement>
    </PageForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import { notifyIf } from '@baserow/modules/core/utils/error'
import PageForm from '@baserow/modules/builder/components/page/PageForm'

export default {
  name: 'CreatePageModal',
  components: { PageForm },
  mixins: [modal],
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async addPage({ name }) {
      this.loading = true
      try {
        const page = await this.$store.dispatch('page/create', {
          builder: this.builder,
          name,
        })
        await this.$router.push({
          name: 'builder-page',
          params: { builderId: this.builder.id, pageId: page.id },
        })
        this.hide()
      } catch (error) {
        notifyIf(error, 'application')
      }
      this.loading = false
    },
  },
}
</script>
