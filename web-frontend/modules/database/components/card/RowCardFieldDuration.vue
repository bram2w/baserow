<template functional>
  <div class="card-text">
    {{ $options.methods.formatValue(props.field, props.value) }}
  </div>
</template>

<script>
import durationField from '@baserow/modules/database/mixins/durationField'

export default {
  height: 16,
  name: 'RowCardFieldDuration',
  mixins: [durationField],
}
</script>
