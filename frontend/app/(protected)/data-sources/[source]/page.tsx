import "server-only";
import sourceTexts from "@/server-data/source-texts.json";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, BookOpen } from "lucide-react";
import { dataSources, sourceKinds } from "@/lib/data-sources";
export default async function SourcePage({
  params,
}: {
  params: Promise<{ source: string }>;
}) {
  const { source: id } = await params;
  // 요청값을 파일 경로로 사용하지 않고 공개 가능한 자료의 허용 목록만 읽는다.
  const source = dataSources.find((s) => s.id === id);
  if (!source) notFound();
  const text = source.file
    ? sourceTexts[source.file as keyof typeof sourceTexts]
    : source.body;
  return (
    <main id="main" className="data-sources-page source-detail-page">
      <Link className="back-home" href="/data-sources">
        <ArrowLeft size={16} />
        데이터 출처로
      </Link>
      <header className="source-detail-heading">
        <span className={`source-kind ${source.kind}`}>
          {sourceKinds[source.kind]}
        </span>
        <h1>{source.title}</h1>
        <p>{source.description}</p>
        <small>
          {source.issuer} · {source.edition}
        </small>
      </header>
      <aside className="source-usage">
        <BookOpen size={21} />
        <div>
          <h2>이 자료는 이렇게 사용합니다</h2>
          <p>{source.usage}</p>
        </div>
      </aside>
      <section className="source-document" aria-label="사용 자료 본문">
        <h2>
          {source.file ? "프로젝트에서 사용한 문서 본문" : "시연 데이터 안내"}
        </h2>
        <pre>{text}</pre>
      </section>
    </main>
  );
}
