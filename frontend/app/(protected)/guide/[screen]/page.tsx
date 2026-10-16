import { notFound } from "next/navigation";
import { GuidePlayer } from "@/components/guide-player";
import { tours } from "@/lib/tours";
export const metadata = { robots: { index: false, follow: false } };
/** 메뉴에 노출하지 않는 안내 전용 경로. 인증은 기존 protected layout을 공유한다. */
export default async function GuidePage({
  params,
}: {
  params: Promise<{ screen: string }>;
}) {
  const { screen } = await params;
  if (!Object.hasOwn(tours, screen)) notFound();
  return <GuidePlayer screen={screen} initialTime={new Date().toISOString()} />;
}
