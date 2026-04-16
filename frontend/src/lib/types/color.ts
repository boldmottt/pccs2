export interface ColorXYZ {
  L: number
  a: number
  b: number
}

export interface ColorWithDelta {
  L: number
  a: number
  b: number
  deltaE?: number
}

export interface ColorMeasurement {
  sci: ColorXYZ
  sce: ColorXYZ
  deltaESciSce?: number
}

/** Convert CIE LAB to RGB for display */
export function convertLabToRgb(L: number, a: number, b: number): { r: number; g: number; b: number } {
  // Simplified conversion - use proper formula in production
  const labToLms = [
    [0.4002, 0.7076, -0.0808],
    [-0.2263, 1.1653, 0.0457],
    [0.0000, 0.0000, 0.9182]
  ]

  // Convert to LMS
  const LMS = labToLms.map(row =>
    row[0] * (L / 100) + row[1] * (a / 127) + row[2] * (b / 127)
  )

  // Convert to XYZ
  const XYZ = [
    LMS[0] * 2.049,
    LMS[1] * 0.5688,
    LMS[2] * 0.3476
  ]

  // Convert to RGB
  const RGB = [
    XYZ[0] * 3.2406 + XYZ[1] * -1.5372 + XYZ[2] * -0.4986,
    XYZ[0] * -0.9689 + XYZ[1] * 1.8758 + XYZ[2] * 0.0415,
    XYZ[0] * 0.0557 + XYZ[1] * -0.2040 + XYZ[2] * 1.0570
  ]

  // Convert to 0-255 range
  return {
    r: Math.round(Math.min(255, Math.max(0, RGB[0] * 255))),
    g: Math.round(Math.min(255, Math.max(0, RGB[1] * 255))),
    b: Math.round(Math.min(255, Math.max(0, RGB[2] * 255)))
  }
}
