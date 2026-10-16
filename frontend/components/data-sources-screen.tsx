"use client";
import Link from "next/link";
import { useState } from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  BookOpen,
  Database,
  FileText,
  FlaskConical,
} from "lucide-react";
import { dataSources, sourceKinds, type DataSource } from "@/lib/data-sources";
const icons = { public: BookOpen, fictional: FileText, demo: FlaskConical };
export function DataSourcesScreen() {
  const [filter, setFilter] = useState<"all" | DataSource["kind"]>("all");
  const items = dataSources.filter(
    (s) => filter === "all" || s.kind === filter,
  );
  return (
    <main id="main" className="data-sources-page">
      <Link href="/" className="back-home">
        <ArrowLeft size={16} />
        메인으로
      </Link>
      <header className="sources-intro">
        <span className="sources-eyebrow">
          <Database size={17} /> DATA SOURCES
        </span>
        <h1>데이터 출처 및 참고자료</h1>
        <p>
          가온 AI가 어떤 자료를 바탕으로 동작하는지 확인하세요.
          <br />
          공개 표준약관과 시연을 위해 만든 가상 문서·데이터를 구분해 안내합니다.
        </p>
      </header>
      <div className="sources-summary" aria-label="사용 자료 요약">
        <div>
          <strong>
            5<span>종</span>
          </strong>
          <span>공개 표준약관</span>
        </div>
        <div>
          <strong>
            7<span>종</span>
          </strong>
          <span>시연용 약관·업무 문서</span>
        </div>
        <div>
          <strong>
            10<span>명</span>
          </strong>
          <span>가상 고객</span>
        </div>
        <div>
          <strong>
            13<span>건</span>
          </strong>
          <span>가상 청구</span>
        </div>
      </div>
      <section aria-label="출처 목록">
        <div className="sources-filters" aria-label="자료 유형">
          {(
            [["all", "전체 자료"], ...Object.entries(sourceKinds)] as [
              typeof filter,
              string,
            ][]
          ).map(([id, label]) => (
            <button
              key={id}
              className={filter === id ? "active" : ""}
              aria-pressed={filter === id}
              onClick={() => setFilter(id)}
            >
              {label}
              <span>
                {id === "all"
                  ? dataSources.length
                  : dataSources.filter((s) => s.kind === id).length}
              </span>
            </button>
          ))}
        </div>
        <div className="sources-grid">
          {items.map((source) => {
            const Icon = icons[source.kind];
            return (
              <article className="source-card" key={source.id}>
                <div className="source-card-heading">
                  <span className="source-symbol">
                    <Icon size={24} />
                  </span>
                  <div>
                    <span className={`source-kind ${source.kind}`}>
                      {sourceKinds[source.kind]}
                    </span>
                    <h2>{source.title}</h2>
                  </div>
                </div>
                <p>{source.description}</p>
                <small>{source.issuer}</small>
                <small>{source.edition}</small>
                <Link
                  href={`/data-sources/${source.id}`}
                  aria-label={`${source.title} 자료 보기`}
                >
                  자료 보기
                  <ArrowUpRight size={18} />
                </Link>
              </article>
            );
          })}
        </div>
      </section>
      <aside className="sources-note">
        <FlaskConical size={22} />
        <div>
          <h2>가상 자료로 구성한 PoC입니다</h2>
          <p>
            실제 보험사 고객 데이터와 연결되어 있지 않습니다. 보험금 지급 여부와
            금액은 판단하지 않으며, 실제 도입 시 사내 약관과 업무 기준에 맞춘
            검증·연동이 필요합니다.
          </p>
        </div>
      </aside>
    </main>
  );
}
