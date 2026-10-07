import { notFound } from "next/navigation";
import { readConfig } from "../../../lib/config";
import { AuthForm } from "../../../components/auth-form";

export const dynamic = "force-dynamic";
export default async function AuthPage({params}: {params: Promise<{view: string}>}) {
  const {view} = await params;
  if (!["sign-in", "sign-up", "verify-email", "forgot-password", "reset-password", "sign-out"].includes(view)) notFound();
  const config = readConfig();
  return <AuthForm view={view} googleEnabled={config.googleEnabled}/>;
}
