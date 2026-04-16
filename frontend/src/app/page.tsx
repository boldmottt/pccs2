import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">PCCS2</h1>
        <p className="text-xl text-gray-600">
          빅데이터 기반 AI 잉크 배합비 추천 시스템
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Link href="/projects" className="block">
          <div className="rounded-lg border border-gray-200 bg-white p-6 hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-semibold mb-2">Projects</h3>
            <p className="text-gray-600">프로젝트 관리</p>
          </div>
        </Link>

        <Link href="/samples" className="block">
          <div className="rounded-lg border border-gray-200 bg-white p-6 hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-semibold mb-2">Samples</h3>
            <p className="text-gray-600">샘플 배합비 관리</p>
          </div>
        </Link>

        <Link href="/inks" className="block">
          <div className="rounded-lg border border-gray-200 bg-white p-6 hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-semibold mb-2">Inks</h3>
            <p className="text-gray-600">잉크 마스터 데이터</p>
          </div>
        </Link>
      </div>
    </div>
  )
}
