import { DemoSessionBoundary } from "@/components/demo-session-boundary";
import { AppHeader } from "@/components/app-header";
import { requireUser } from "@/lib/auth";

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await requireUser();
  return (
    <div className="app-frame">
      <DemoSessionBoundary />
      <AppHeader user={user} />
      {children}
    </div>
  );
}
