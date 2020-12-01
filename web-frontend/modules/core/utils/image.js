/**
 * Generates a cropped thumbnail that has the provided dimensions. The source image
 * is not stretched into the right format, but is is cropped. So it could be part
 * of the image is not visible anymore.
 */
export function generateThumbnail(source, targetWidth, targetHeight) {
  return new Promise((resolve) => {
    const sourceImage = new Image()
    sourceImage.onload = function (f) {
      const canvas = document.createElement('canvas')
      canvas.width = targetWidth
      canvas.height = targetHeight

      if (sourceImage.width === sourceImage.height) {
        canvas
          .getContext('2d')
          .drawImage(sourceImage, 0, 0, targetWidth, targetHeight)
      } else {
        const minVal = Math.min(sourceImage.width, sourceImage.height)
        let sourceX = 0
        let sourceY = 0

        if (sourceImage.width > sourceImage.height) {
          sourceX = (sourceImage.width - minVal) / 2
        } else {
          sourceY = (sourceImage.height - minVal) / 2
        }

        canvas
          .getContext('2d')
          .drawImage(
            sourceImage,
            sourceX,
            sourceY,
            minVal,
            minVal,
            0,
            0,
            targetWidth,
            targetHeight
          )
      }
      resolve(canvas.toDataURL())
    }
    sourceImage.src = source
  })
}
