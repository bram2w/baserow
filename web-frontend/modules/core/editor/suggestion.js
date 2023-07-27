import Vue from 'vue'

function updateComponentProps(component, props) {
  for (const key of ['command', 'query']) {
    Vue.set(component, key, props[key])
  }
}

export default ({ component }) => ({
  render: () => {
    return {
      onStart: (props) => {
        if (!props.clientRect) {
          return
        }

        updateComponentProps(component, props)
        component.show()
      },

      onUpdate(props) {
        updateComponentProps(component, props)
      },

      onKeyDown(props) {
        if (props.event.key === 'Escape') {
          if (component.open) {
            props.event.preventDefault()
            props.event.stopPropagation()
            component.hide()
          }
          return true
        }

        return component.onKeyDown({ event: props.event })
      },

      onExit() {
        component.hide()
      },
    }
  },
})
