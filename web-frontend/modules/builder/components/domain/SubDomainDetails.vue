<template>
  <div>
    <p>
      {{ $t('subDomainDetails.text') }}
    </p>
    <div class="actions actions--right">
      <a
        class="button button--error"
        :class="{ 'button--loading': domain._.loading }"
        @click="$emit('delete')"
      >
        {{ $t('action.delete') }}
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SubDomainDetails',
  props: {
    domain: {
      type: Object,
      required: true,
    },
  },
}
</script>
