import type { SuccessFlag } from '@/lib/types/project'

export function SuccessFlagBadge({ flag }: { flag: SuccessFlag }) {
  const style =
    flag === 'SUCCESS'
      ? 'bg-green-100 text-green-700'
      : flag === 'FAILED'
        ? 'bg-red-100 text-red-700'
        : 'bg-gray-100 text-gray-600'
  const label = flag === 'SUCCESS' ? '성공' : flag === 'FAILED' ? '실패' : '대기'
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${style}`}>{label}</span>
}
