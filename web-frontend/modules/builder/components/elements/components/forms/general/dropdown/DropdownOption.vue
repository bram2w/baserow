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
      <Button
        class="control"
        icon="iconoir-trash"
        type="ghost"
        @click="$emit('delete')"
      ></Button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DropdownOption',
  props: {
    option: {
      type: Object,
      required: true,
    },
  },
}
</script>
