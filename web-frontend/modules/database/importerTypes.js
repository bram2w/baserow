import { Registerable } from '@baserow/modules/core/registry'

import TableCSVImporter from '@baserow/modules/database/components/table/TableCSVImporter'
import TablePasteImporter from '@baserow/modules/database/components/table/TablePasteImporter'
import TableXMLImporter from '@baserow/modules/database/components/table/TableXMLImporter'
import TableJSONImporter from '@baserow/modules/database/components/table/TableJSONImporter'

export class ImporterType extends Registerable {
  /**
   * Should return a font awesome class name related to the icon that must be displayed
   * to the user.
   */
  getIconClass() {
    throw new Error('The icon class of an importer type must be set.')
  }

  /**
   * Should return a human readable name that indicating what the importer does.
   */
  getName() {
    throw new Error('The name of an importer type must be set.')
  }

  /**
   * Should return the component that is added to the CreateTableModal when the
   * importer is chosen. It should handle all the user input and additional form
   * fields and it should generate a compatible data object that must be added to
   * the form values.
   */
  getFormComponent() {
    return null
  }

  constructor() {
    super()
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.name = this.getName()

    if (this.type === null) {
      throw new Error('The type name of an importer type must be set.')
    }
  }

  serialize() {
    return {
      type: this.type,
      iconClass: this.iconClass,
      name: this.name,
    }
  }
}

export class CSVImporterType extends ImporterType {
  getType() {
    return 'csv'
  }

  getIconClass() {
    return 'file-csv'
  }

  getName() {
    return 'Import a CSV file'
  }

  getFormComponent() {
    return TableCSVImporter
  }
}

export class PasteImporterType extends ImporterType {
  getType() {
    return 'paste'
  }

  getIconClass() {
    return 'paste'
  }

  getName() {
    return 'Paste table data'
  }

  getFormComponent() {
    return TablePasteImporter
  }
}

export class XMLImporterType extends ImporterType {
  getType() {
    return 'xml'
  }

  getIconClass() {
    return 'file-code'
  }

  getName() {
    return 'Import an XML file'
  }

  getFormComponent() {
    return TableXMLImporter
  }
}

export class JSONImporterType extends ImporterType {
  getType() {
    return 'json'
  }

  getIconClass() {
    return 'file-code'
  }

  getName() {
    return 'Import a JSON file'
  }

  getFormComponent() {
    return TableJSONImporter
  }
}
