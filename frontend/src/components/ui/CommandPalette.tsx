import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Search, LayoutDashboard, ShieldCheck, Database, AlertCircle, FileText, PlayCircle, X } from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        isOpen ? onClose() : null;
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const commands = [
    { label: "Go to Command Center", route: "/command-center", icon: LayoutDashboard, category: "Navigation" },
    { label: "Go to Decisions", route: "/decisions", icon: ShieldCheck, category: "Navigation" },
    { label: "Go to Evidence", route: "/evidence", icon: Database, category: "Navigation" },
    { label: "Go to Risk", route: "/risk", icon: AlertCircle, category: "Navigation" },
    { label: "Go to Audit", route: "/audit", icon: FileText, category: "Navigation" },
    { label: "Go to Simulator", route: "/simulator", icon: PlayCircle, category: "Navigation" },
  ];

  const filteredCommands = commands.filter((cmd) =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (route: string) => {
    navigate(route);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-background-secondary border border-border-subtle rounded-card shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center px-4 border-b border-border-subtle bg-background-surface">
          <Search className="h-4 w-4 text-text-muted mr-3 stroke-[2.5]" />
          <input
            type="text"
            placeholder="Type a command or search decisions..."
            className="w-full bg-transparent py-3 text-sm text-text-primary placeholder-text-muted outline-none font-sans"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <button onClick={onClose} className="p-1 text-text-muted hover:text-text-primary rounded">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="max-h-72 overflow-y-auto p-2 space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="p-4 text-center text-xs text-text-muted font-mono">No matching commands found.</div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={idx}
                  onClick={() => handleSelect(cmd.route)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-control text-xs text-text-primary hover:bg-background-hover hover:text-accent-infra transition-colors text-left group"
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="h-4 w-4 text-text-muted group-hover:text-accent-infra" />
                    <span className="font-medium">{cmd.label}</span>
                  </div>
                  <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">{cmd.category}</span>
                </button>
              );
            })
          )}
        </div>

        <div className="px-4 py-2 border-t border-border-subtle bg-background-primary flex items-center justify-between text-[11px] text-text-muted font-mono">
          <span>Navigate with ↑ ↓ and Enter</span>
          <span>ESC to close</span>
        </div>
      </div>
    </div>
  );
};
