import { notFound } from "next/navigation";
import { requireUser } from "@/lib/auth";
import { workspacePages } from "@/lib/navigation";
import { ClaimDetail, ClaimPicker } from "@/components/claim-screens";
import { ComingSoon } from "@/components/coming-soon";

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
  return <ComingSoon {...page} />;
}
