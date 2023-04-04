import * as elementTypes from '@baserow/modules/builder/elementTypes'

const getPropsOfComponent = (component) => {
  let props = Object.keys(component.props || [])

  if (component.mixins) {
    component.mixins.forEach((mixin) => {
      props = props.concat(Object.keys(mixin.props || []))
    })
  }

  return props
}

describe('elementTypes', () => {
  test.each(Object.values(elementTypes))(
    'test that properties mapped for the element type exist on the component as prop',
    (ElementType) => {
      const elementType = new ElementType(expect.anything())

      if (elementType.component) {
        const propsInMapping = Object.keys(
          elementType.getComponentProps(expect.anything())
        )

        const propsOnComponent = getPropsOfComponent(elementType.component)

        propsInMapping.forEach((prop) => {
          expect(propsOnComponent).toContain(prop)
        })
      }
    }
  )
})
