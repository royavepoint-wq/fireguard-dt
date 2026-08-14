"use client";

import { type ReactNode, useState, useSyncExternalStore } from "react";
import { Menu } from "lucide-react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const presentationMode = pathname === "/presentation";
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const sidebarCollapsed = useSyncExternalStore(
    (onStoreChange) => {
      window.addEventListener("storage", onStoreChange);
      window.addEventListener("fireguard-sidebar-collapsed-change", onStoreChange as EventListener);
      return () => {
        window.removeEventListener("storage", onStoreChange);
        window.removeEventListener("fireguard-sidebar-collapsed-change", onStoreChange as EventListener);
      };
    },
    () => {
      try {
        return window.localStorage.getItem("fireguard-sidebar-collapsed") === "true";
      } catch {
        return false;
      }
    },
    () => false,
  );

  function setSidebarCollapsed(nextValue: boolean) {
    try {
      window.localStorage.setItem("fireguard-sidebar-collapsed", String(nextValue));
      window.dispatchEvent(new Event("fireguard-sidebar-collapsed-change"));
    } catch {
      // Ignore storage failures in restricted environments.
    }
  }

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-[var(--bg-deep)] text-white lg:flex">
      {mobileSidebarOpen && !presentationMode ? (
        <button
          type="button"
          aria-label="Close navigation drawer"
          className="fixed inset-0 z-30 bg-black/45 lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      ) : null}

      {!presentationMode ? (
        <Sidebar
          collapsed={sidebarCollapsed}
          mobileOpen={mobileSidebarOpen}
          onCloseMobile={() => setMobileSidebarOpen(false)}
          onNavigateMobile={() => setMobileSidebarOpen(false)}
          onToggleCollapsed={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      ) : null}

      <div className="min-w-0 flex-1 bg-[var(--bg-deep)]">
        <header className={`flex items-center gap-3 border-b border-white/10 bg-[var(--bg-deep)] px-4 py-3 lg:hidden ${presentationMode ? "hidden" : ""}`}>
          <button
            type="button"
            aria-label="Open navigation drawer"
            className="rounded-xl border border-white/10 bg-white/5 p-2 text-white transition hover:border-cyan-400/40 hover:bg-white/10"
            onClick={() => setMobileSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </button>
          <div>
            <p className="text-sm font-semibold tracking-wide text-white">FireGuard DT</p>
            <p className="text-xs text-[var(--fg-muted)]">Emergency Digital Twin</p>
          </div>
        </header>

        <main className="min-w-0 w-full bg-[var(--bg-deep)]">
          <div className="min-w-0 w-full px-4 py-6 md:px-6 xl:px-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
