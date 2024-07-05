<template>
  <div class="dropdown-option">
    <FormInput
      :value="option.value"
      @input="$emit('update', { value: $event })"
    />
    <FormInput
      :value="option.name"
      @input="$emit('update', { name: $event })"
    />
    <div class="dropdown-option__delete">
      <ButtonIcon icon="iconoir-bin" @click="$emit('delete')"></ButtonIcon>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChoiceOption',
  props: {
    option: {
      type: Object,
      required: true,
    },
  },
}
</script>
