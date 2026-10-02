import { NavLink, Outlet } from "react-router-dom";
import { History, Home, LayoutTemplate, Settings, Waves } from "lucide-react";
import { cn } from "@/shared/lib/utils";

const navItems = [
  { to: "/", label: "Nova transcrição", icon: Home },
  { to: "/history", label: "Histórico", icon: History },
  { to: "/templates", label: "Templates", icon: LayoutTemplate },
  { to: "/settings", label: "Configurações", icon: Settings },
];

export function AppLayout() {
  return (
    <div className="min-h-screen flex bg-background">
      <aside className="w-64 border-r bg-card flex flex-col">
        <div className="h-16 px-6 flex items-center gap-2 border-b">
          <Waves className="h-5 w-5 text-primary" />
          <span className="font-semibold tracking-tight">LocalTranscriber</span>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                  "text-muted-foreground hover:text-foreground hover:bg-accent",
                  isActive && "bg-accent text-foreground font-medium",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t text-xs text-muted-foreground">
          v0.2 · 100% local
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
