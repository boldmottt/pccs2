// eslint-config-next@16은 ESLint flat config 배열을 직접 export 한다.
import coreWebVitals from 'eslint-config-next/core-web-vitals'

const eslintConfig = [
  ...coreWebVitals,
  {
    ignores: ['.next/**', 'node_modules/**', 'out/**'],
  },
]

export default eslintConfig
