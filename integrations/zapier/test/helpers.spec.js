const { mapBaserowFieldTypesToZapierTypes } = require('../src/helpers')

describe('helpers', () => {
  describe('mapBaserowFieldTypesToZapierTypes ', () => {
    it('text field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'text',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        text_default: ''
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'string'
      })
    })

    it('long_text field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'long_text',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'text'
      })
    })

    it('url field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'url',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'string'
      })
    })

    it('email field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'email',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'string'
      })
    })

    it('number field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'number',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        number_decimal_places: 0,
        number_negative: false,
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'integer'
      })
    })

    it('number field with decimal places', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'number',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        number_decimal_places: 1,
        number_negative: false,
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'float'
      })
    })

    it('rating field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'rating',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        max_value: 5,
        color: 'red',
        style: 'star'
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'integer'
      })
    })

    it('boolean field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'boolean',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false
      })).toMatchObject({
          key: 'Name',
          label: 'Name',
          type: 'boolean'
      })
    })

    it('date field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'date',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        date_format: 'ISO',
        date_include_time: false,
        date_time_format: '12'
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'date'
      })
    })

    it('date field with time', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'date',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        date_format: 'ISO',
        date_include_time: true,
        date_time_format: '24'
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'datetime'
      })
    })

    it('last_modified field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'last_modified',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: true,
        date_format: 'ISO',
        date_include_time: true,
        date_time_format: '24'
      })).toBeUndefined()
    })

    it('created_on field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'created_on',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: true,
        date_format: 'EU',
        date_include_time: false,
        date_time_format: '12'
      })).toBeUndefined()
    })

    it('link_row field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'link_row',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        link_row_table_id: 1,
        link_row_related_field_id: 2,
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'integer',
        helpText: `Provide row ids that you want to link to.`,
        list: true,
      })
    })

    it('file field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'file',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
      })).toBeUndefined()
    })

    it('single_select field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'single_select',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        select_options: [
          {id: 1, value: 'test', color: 'red'},
          {id: 2, value: 'value', color: 'green'}
        ]
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'string',
        choices: {
          '1': 'test',
          '2': 'value',
        }
      })
    })

    it('multiple_select field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'multiple_select',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
        select_options: [
          {id: 1, value: 'test', color: 'red'},
          {id: 2, value: 'value', color: 'green'}
        ]
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'string',
        choices: {
          '1': 'test',
          '2': 'value',
        },
        list: true
      })
    })

    it('phone_number field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'phone_number',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'string'
      })
    })

    it('formula field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'formula',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: true
      })).toBeUndefined()
    })

    it('lookup field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'lookup',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: true,
      })).toBeUndefined()
    })

    it('multiple_collaborators field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'multiple_collaborators',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false,
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'integer',
        helpText: `Provide user ids that you want to link to.`,
        list: true
      })
    })

    it('unknown field', () => {
      expect(mapBaserowFieldTypesToZapierTypes({
        id: 1,
        type: 'unknown_field_type',
        name: 'Name',
        order: 0,
        primary: false,
        read_only: false
      })).toMatchObject({
        key: 'Name',
        label: 'Name',
        type: 'string'
      })
    })
  })
})
