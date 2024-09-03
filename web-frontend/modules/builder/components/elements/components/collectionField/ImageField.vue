<template>
  <div class="image-field">
    <ABImage
      v-for="(image, index) in images"
      :key="`${index}-${image.src}`"
      :src="image.src"
      :alt="image.alt"
      :lazy="true"
    ></ABImage>
  </div>
</template>

<script>
import collectionField from '@baserow/modules/builder/mixins/collectionField'

export default {
  name: 'ImageField',
  mixins: [collectionField],
  props: {
    images: {
      type: Array,
      required: true,
    },
  },
}
</script>
