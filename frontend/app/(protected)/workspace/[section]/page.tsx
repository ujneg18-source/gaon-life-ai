import { notFound } from "next/navigation";
import { requireUser } from "@/lib/auth";
import { workspacePages } from "@/lib/navigation";
import { ClaimDetail, ClaimPicker } from "@/components/claim-screens";
import { ReviewScreen } from "@/components/review-screen";
import {
  SupplementScreen,
  HistoryScreen,
  OperationsScreen,
} from "@/components/operations-screens";

export default async function SectionPage({
  params,
  searchParams,
}: {
  params: Promise<{ section: string }>;
  searchParams: Promise<{ claim?: string }>;
}) {
  const { section } = await params;
  const user = await requireUser();
  const page = workspacePages.find((item) => item.slug === section);
  // URL 직접 접근도 서버에서 막는다. 메뉴 숨김만으로 권한을 보장할 수 없다.
  if (!page || ("adminOnly" in page && page.adminOnly && user.role !== "admin"))
    notFound();
  const query = await searchParams;
  if (section === "detail")
    return query.claim ? (
      <ClaimDetail claimId={query.claim} readOnly={user.role === "admin"} />
    ) : (
      <ClaimPicker section={section} />
    );
  if (section === "review")
    return query.claim ? (
      <ReviewScreen claimId={query.claim} readOnly={user.role === "admin"} />
    ) : (
      <ClaimPicker section={section} />
    );
  if (section === "supplement")
    return query.claim ? (
      <SupplementScreen
        key={query.claim ?? "all"}
        claimId={query.claim}
        readOnly={user.role === "admin"}
      />
    ) : (
      <ClaimPicker section={section} />
    );
  if (section === "history")
    return query.claim ? (
      <HistoryScreen claimId={query.claim} />
    ) : (
      <ClaimPicker section={section} />
    );
  if (section === "operations") return <OperationsScreen />;
  notFound();
}
