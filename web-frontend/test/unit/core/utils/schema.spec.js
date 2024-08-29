import { extractSubSchema } from '@baserow/modules/core/utils/schema'

describe('extractSubSchema', () => {
  const schema = {
    type: 'object',
    properties: {
      name: { type: 'string', required: true },
      age: { type: 'integer', required: true },
      email: { type: 'string', required: false },
      address: {
        type: 'object',
        properties: {
          street: { type: 'string', required: true },
          city: { type: 'string', required: true, forTestCity: true },
          zipCode: { type: 'string', required: false },
        },
      },
      contacts: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            phone: { type: 'string', required: true, forTestPhone: true },
            email: { type: 'string', required: false },
          },
        },
      },
    },
  }

  test('should extract a simple property', () => {
    const paths = ['name']
    const subSchema = extractSubSchema(schema, paths)
    expect(subSchema).toEqual({ type: 'string', required: true })
  })

  test('should extract a nested property', () => {
    const paths = ['address', 'city']
    const subSchema = extractSubSchema(schema, paths)
    expect(subSchema).toEqual({
      type: 'string',
      required: true,
      forTestCity: true,
    })
  })

  test('should extract a property from an array of objects', () => {
    const paths = ['contacts', 'phone']
    const subSchema = extractSubSchema(schema, paths)
    expect(subSchema).toEqual({
      type: 'string',
      required: true,
      forTestPhone: true,
    })
  })

  test('should return an empty object for an invalid path', () => {
    const paths = ['invalid', 'path']
    const subSchema = extractSubSchema(schema, paths)
    expect(subSchema).toEqual(null)
  })

  test('should handle deep nesting with arrays and objects', () => {
    const paths = ['contacts']
    const subSchema = extractSubSchema(schema, paths)
    expect(subSchema).toEqual({
      type: 'array',
      items: {
        type: 'object',
        properties: {
          phone: { type: 'string', required: true, forTestPhone: true },
          email: { type: 'string', required: false },
        },
      },
    })
  })
})
