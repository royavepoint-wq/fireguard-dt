"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose, PanelLeftOpen, ShieldAlert, X } from "lucide-react";
import { navItems } from "@/lib/navigation";

type SidebarProps = {
  collapsed: boolean;
  mobileOpen: boolean;
  onToggleCollapsed: () => void;
  onCloseMobile: () => void;
  onNavigateMobile: () => void;
};

export function Sidebar({ collapsed, mobileOpen, onToggleCollapsed, onCloseMobile, onNavigateMobile }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={`sidebar-shell fixed inset-y-0 left-0 z-40 flex w-[272px] -translate-x-full flex-col border-white/10 bg-[var(--bg-deep)]/98 shadow-2xl shadow-black/30 transition-[width,transform] duration-200 ease-out lg:static lg:z-auto lg:h-screen lg:translate-x-0 lg:shadow-none ${mobileOpen ? "translate-x-0" : ""} ${collapsed ? "lg:w-20" : "lg:w-[272px]"}`}
    >
      <div className="flex min-h-0 flex-1 flex-col gap-4 p-4 lg:p-3">
        <div className="flex items-start justify-between gap-3 border-b border-white/10 pb-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="rounded-lg bg-cyan-500/20 p-2 text-cyan-300">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div className={collapsed ? "lg:hidden" : "min-w-0"}>
              <p className="text-sm font-semibold tracking-wide text-white">FireGuard DT</p>
              <p className="text-xs text-[var(--fg-muted)]">Emergency Digital Twin</p>
            </div>
          </div>

          <button
            type="button"
            aria-label={mobileOpen ? "Close navigation drawer" : collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={mobileOpen ? "Close" : collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="rounded-lg border border-white/10 bg-white/5 p-2 text-white transition hover:border-cyan-400/40 hover:bg-white/10"
            onClick={mobileOpen ? onCloseMobile : onToggleCollapsed}
          >
            {mobileOpen ? <X className="h-4 w-4" /> : collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </button>
        </div>

        <div className="rounded-2xl border border-cyan-400/15 bg-cyan-400/8 px-3 py-2 text-xs text-cyan-100">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_0_4px_rgba(57,217,138,0.14)]" />
            <span className={collapsed ? "lg:hidden" : ""}>System Live</span>
          </div>
        </div>

        <nav className="min-h-0 flex-1">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  title={item.label}
                  aria-label={item.label}
                  onClick={onNavigateMobile}
                  className={`nav-item ${isActive ? "nav-item-active" : ""} ${collapsed ? "lg:justify-center lg:px-3" : ""}`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className={collapsed ? "lg:hidden" : ""}>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

        <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-xs text-[var(--fg-muted)]">
          <p className={collapsed ? "lg:hidden" : ""}>Operational cockpit for fire prediction, evacuation, response, and governance.</p>
        </div>
      </div>
    </aside>
  );
}
