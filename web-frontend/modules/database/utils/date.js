const dateMapping = {
  EU: {
    momentFormat: 'DD/MM/YYYY',
    humanFormat: 'dd/mm/yyyy',
  },
  US: {
    momentFormat: 'MM/DD/YYYY',
    humanFormat: 'mm/dd/yyyy',
  },
  ISO: {
    momentFormat: 'YYYY-MM-DD',
    humanFormat: 'yyyy-mm-dd',
  },
}

const timeMapping = {
  12: {
    momentFormat: 'hh:mm A',
    humanFormat: 'hh:mm AM',
  },
  24: {
    momentFormat: 'HH:mm',
    humanFormat: 'hh:mm',
  },
}

export const getDateMomentFormat = (type) => {
  if (!Object.prototype.hasOwnProperty.call(dateMapping, type)) {
    throw new Error(`${type} wasn't found in the date mapping.`)
  }
  return dateMapping[type].momentFormat
}

export const getTimeMomentFormat = (type) => {
  if (!Object.prototype.hasOwnProperty.call(timeMapping, type)) {
    throw new Error(`${type} wasn't found in the time mapping.`)
  }
  return timeMapping[type].momentFormat
}

export const getDateHumanReadableFormat = (type) => {
  if (!Object.prototype.hasOwnProperty.call(dateMapping, type)) {
    throw new Error(`${type} wasn't found in the date mapping.`)
  }
  return dateMapping[type].humanFormat
}

export const getTimeHumanReadableFormat = (type) => {
  if (!Object.prototype.hasOwnProperty.call(timeMapping, type)) {
    throw new Error(`${type} wasn't found in the time mapping.`)
  }
  return timeMapping[type].humanFormat
}
