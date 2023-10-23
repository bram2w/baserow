<template>
  <FileFieldModal
    v-if="Array.isArray(value)"
    ref="fileModal"
    :files="Array.isArray(value) ? value : [value]"
    :read-only="true"
  ></FileFieldModal>
</template>

<script>
import FileFieldModal from '@baserow/modules/database/components/field/FileFieldModal'

export default {
  name: 'SingleFileArrayModal',
  components: { FileFieldModal },
  props: {
    value: {
      type: Array,
      required: true,
    },
  },
  computed: {
    open() {
      return this.$refs.fileModal.open
    },
  },
  methods: {
    show(index) {
      this.$refs.fileModal.show(index)
    },
  },
}
</script>
