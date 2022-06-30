<template>
  <a @click="redirect">
    <slot></slot>
    <Modal ref="modal" @hidden="cancel">
      <div class="redirect-modal">
        <div class="redirect-modal__title">
          {{ $t('redirectToBaserowModal.title') }}
        </div>
        <p>{{ $t('redirectToBaserowModal.content') }}</p>
        <div class="redirect-modal__from-to">
          <client-only>{{ getHostname() }}</client-only>
          <i class="fas fa-arrow-right redirect-modal__from-to-icon"></i>
          baserow.io
        </div>
        <div class="redirect-modal__loading">
          <div class="loading"></div>
        </div>
      </div>
    </Modal>
  </a>
</template>

<script>
export default {
  name: 'RedirectToBaserowModal',
  props: {
    href: {
      type: String,
      required: true,
    },
  },
  methods: {
    redirect() {
      this.$refs.modal.show()
      this.redirectTimeout = setTimeout(() => {
        window.location.href = this.href
      }, 3000)
    },
    cancel() {
      clearTimeout(this.redirectTimeout)
    },
    getHostname() {
      return process.client ? window.location.hostname : ''
    },
  },
}
</script>
