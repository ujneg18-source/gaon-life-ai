import { notFound } from "next/navigation";
import { requireUser } from "@/lib/auth";
import { workspacePages } from "@/lib/navigation";
import { ComingSoon } from "@/components/coming-soon";

export default async function SectionPage({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = await params;
  const user = await requireUser();
  const page = workspacePages.find((item) => item.slug === section);
  // URL 직접 접근도 서버에서 막는다. 메뉴 숨김만으로 권한을 보장할 수 없다.
  if (!page || ("adminOnly" in page && page.adminOnly && user.role !== "admin"))
    notFound();
  return <ComingSoon {...page} />;
}
