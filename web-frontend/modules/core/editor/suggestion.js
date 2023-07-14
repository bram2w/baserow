import { VueRenderer } from '@tiptap/vue-2'

// items is already used in our dropdown, so remap it to collaborators and hide the search bar
const remapPropsForDropdown = (props) => {
  const { items, ...rest } = props
  return {
    ...rest,
    collaborators: items,
    showSearch: false,
    addEmptyItem: false,
  }
}

export default ({ VueComponent, context }) => ({
  items: ({ query }) => {
    const { $store } = context
    const workspace = $store.getters['workspace/getSelected']
    return workspace.users.filter(
      (user) =>
        user.name.toLowerCase().includes(query.toLowerCase()) &&
        user.to_be_deleted === false
    )
  },

  render: () => {
    let component

    return {
      onStart: (props) => {
        const { $el, $i18n, $nextTick } = context
        component = new VueRenderer(VueComponent, {
          parent: this,
          propsData: remapPropsForDropdown(props),
          i18n: $i18n,
          nextTick: $nextTick,
        })

        if (!props.clientRect) {
          return
        }

        $el.appendChild(component.element)
        component.ref.show()
      },

      onUpdate(props) {
        component.updateProps(remapPropsForDropdown(props))
      },

      onKeyDown(props) {
        if (props.event.key === 'Escape') {
          if (component.ref?.open) {
            props.event.preventDefault()
            props.event.stopPropagation()
            component.ref?.hide()
          }
          return true
        }

        return component.ref?.onKeyDown(remapPropsForDropdown(props))
      },

      onExit() {
        const { $el } = context
        component.ref?.hide()
        component.destroy()
        try {
          $el.removeChild(component.ref.$el)
        } catch (e) {} // hot-reload might make this fail
      },
    }
  },
})
