/**
 * Extracts a list of files from a dom event when it is triggered. Supports both input
 * and drag and drop file uploads.
 *
 * @param event
 * @returns {null}
 */
export function getFilesFromEvent(event) {
  if (event.target?.files) {
    // Files via the file upload input.
    return event.target.files
  }

  if (event.dataTransfer) {
    // Files via drag and drop.
    return event.dataTransfer.files
  }

  return []
}
