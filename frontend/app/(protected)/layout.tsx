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
      <AppHeader user={user} />
      {children}
    </div>
  );
}
