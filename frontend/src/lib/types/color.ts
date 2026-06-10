/** CIE L*a*b* color value (백엔드 계약: {L, a, b}) */
export interface Lab {
  L: number
  a: number
  b: number
}

/** CIE76 색차 (클라이언트 표시용 근사값) */
export function deltaE76(c1: Lab, c2: Lab): number {
  const dl = c1.L - c2.L
  const da = c1.a - c2.a
  const db = c1.b - c2.b
  return Math.sqrt(dl * dl + da * da + db * db)
}

/** CIE L*a*b* → sRGB 변환 (D65 기준, 화면 표시용) */
export function convertLabToRgb(L: number, a: number, b: number): { r: number; g: number; b: number } {
  // Lab → XYZ
  const fy = (L + 16) / 116
  const fx = fy + a / 500
  const fz = fy - b / 200

  const d = 6 / 29
  const fInv = (t: number) => (t > d ? t * t * t : 3 * d * d * (t - 4 / 29))

  // D65 reference white
  const X = 0.95047 * fInv(fx)
  const Y = 1.0 * fInv(fy)
  const Z = 1.08883 * fInv(fz)

  // XYZ → linear sRGB
  const rLin = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
  const gLin = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
  const bLin = 0.0557 * X - 0.204 * Y + 1.057 * Z

  // gamma correction
  const gamma = (c: number) => {
    const v = c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(Math.max(c, 0), 1 / 2.4) - 0.055
    return Math.round(Math.min(255, Math.max(0, v * 255)))
  }

  return { r: gamma(rLin), g: gamma(gLin), b: gamma(bLin) }
}

/** Lab 값을 CSS rgb() 문자열로 변환 */
export function labToCss(color: Lab): string {
  const rgb = convertLabToRgb(color.L, color.a, color.b)
  return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`
}
