<template>
  <div class="dropdown-option">
    <FormInput
      small
      :value="option.value"
      @input="$emit('update', { value: $event })"
    />
    <FormInput
      small
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
