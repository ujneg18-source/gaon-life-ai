import { requireUser } from "@/lib/auth";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await requireUser();
  return (
    <WorkspaceShell admin={user.role === "admin"}>{children}</WorkspaceShell>
  );
}
