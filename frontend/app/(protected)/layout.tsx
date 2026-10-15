import { Brand } from "@/components/brand";
import { LogoutButton } from "@/components/logout-button";
import { requireUser, roleLabel } from "@/lib/auth";

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await requireUser();
  return (
    <div className="app-frame">
      <header className="topbar">
        <Brand />
        <div className="user-menu">
          <span>
            <strong>{user.name}</strong>
            <span className="user-role">{roleLabel[user.role]}</span>
          </span>
          <LogoutButton />
        </div>
      </header>
      {children}
    </div>
  );
}
