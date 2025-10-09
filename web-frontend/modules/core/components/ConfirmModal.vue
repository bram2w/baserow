<template>
  <Modal small>
    <h2 class="box__title">
      {{ title }}
    </h2>
    <p>
      {{ message }}
    </p>
    <div>
      <div class="actions">
        <ul class="action__links">
          <li>
            <a
              @click.prevent="
                $emit('cancel', $event)
                hide()
              "
              >{{ $t('action.cancel') }}</a
            >
          </li>
        </ul>

        <Button
          :type="confirmButtonType"
          @click.prevent="
            $emit('confirm', $event)
            hide()
          "
        >
          {{ confirmButtonText }}
        </Button>
      </div>
    </div>
  </Modal>
</template>

<script>
import Modal from '@baserow/modules/core/components/Modal'
import Button from '@baserow/modules/core/components/Button'
import modal from '@baserow/modules/core/mixins/modal'

export default {
  name: 'ConfirmModal',
  components: {
    Modal,
    Button
  },
  mixins: [modal],
  props: {
    title: {
      type: String,
      default: 'Confirm'
    },
    message: {
      type: String,
      default: 'Are you sure?'
    },
    confirmButtonText: {
      type: String,
      default: 'Confirm'
    },
    confirmButtonType: {
      type: String,
      default: 'primary'
    }
  }
}
</script>