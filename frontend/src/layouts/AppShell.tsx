import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Command, Menu, X } from "lucide-react";
import { CommandPalette } from "../components/ui/CommandPalette";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const location = useLocation();
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems: { label: string; route: string; alias?: string }[] = [
    { label: "Test Payment Lab", route: "/test-payment" },
    { label: "Refund Risk", route: "/refund-risk", alias: "/" },
    { label: "Decisions", route: "/decisions" },
    { label: "Evidence", route: "/evidence" },
    { label: "Risk", route: "/risk" },
    { label: "Audit", route: "/audit" },
    { label: "Simulator", route: "/simulator" },
  ];

  return (
    <div className="min-h-screen w-full flex flex-col bg-[#07090C] text-[#F5F7FA] font-sans overflow-x-hidden">
      {/* 1. Fixed/Sticky Top Navigation Header */}
      <header className="sticky top-0 z-50 w-full bg-[#07090C]/90 backdrop-blur-md border-b border-white/[0.08] px-4 sm:px-8 py-3.5 transition-all duration-200">
        <div className="max-w-[1400px] mx-auto flex items-center justify-between gap-4">
          {/* Left: Text-only Brand Wordmark */}
          <Link to="/refund-risk" className="flex items-center gap-2 group">
            <span className="font-sans font-extrabold text-lg text-[#F5F7FA] tracking-[-0.02em] leading-none">
              TRUSTLEDGER
            </span>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-8 text-[13px] font-sans">
            {navItems.map((item) => {
              const isActive =
                location.pathname === item.route || (item.alias && location.pathname === item.alias);

              return (
                <Link
                  key={item.route}
                  to={item.route}
                  className={`relative py-1 transition-colors ${
                    isActive
                      ? "text-[#F5F7FA] font-semibold"
                      : "text-[#A3ACB8] hover:text-[#F5F7FA]"
                  }`}
                >
                  <span>{item.label}</span>
                  {isActive && (
                    <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#4F8CFF] rounded-full" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Right: Status Indicator & Search Trigger */}
          <div className="hidden sm:flex items-center gap-3">
            <button
              onClick={() => setIsCommandOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-[#0C1015] hover:bg-[#11161D] border border-white/[0.08] rounded-md text-xs text-[#68717D] transition-all font-mono"
            >
              <Command className="h-3.5 w-3.5" />
              <span>(Ctrl+K)</span>
            </button>

            <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0C1015] border border-white/[0.08] rounded-md text-xs font-mono">
              <span className="h-2 w-2 rounded-full bg-[#36D98A] animate-pulse" />
              <span className="text-[#A3ACB8] font-medium">BACKEND ONLINE</span>
              <span className="text-white/20">•</span>
              <span className="text-[#8B7CFF] font-medium">NVIDIA</span>
            </div>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-2 text-[#A3ACB8] hover:text-[#F5F7FA]"
          >
            {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Dropdown Overlay */}
        {isMobileMenuOpen && (
          <div className="lg:hidden mt-3 pt-3 border-t border-white/[0.08] flex flex-col space-y-1.5 px-2 pb-2 text-sm font-sans">
            {navItems.map((item) => (
              <Link
                key={item.route}
                to={item.route}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`py-2 px-3 rounded-md ${
                  location.pathname === item.route
                    ? "bg-[#4F8CFF]/15 text-[#F5F7FA] font-semibold"
                    : "text-[#A3ACB8] hover:bg-[#0C1015]"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        )}
      </header>

      {/* 2. Main Page Viewport */}
      <main className="flex-1 max-w-[1400px] w-full mx-auto px-4 sm:px-8 lg:px-12 py-10 space-y-12">
        {children}
      </main>

      {/* 3. Clean Minimal Footer */}
      <footer className="w-full bg-[#07090C] border-t border-white/[0.08] py-8 px-4 sm:px-8 lg:px-12 mt-16 font-sans text-xs">
        <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-[#68717D]">
          <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4">
            <span className="font-extrabold text-[#F5F7FA] tracking-tight">TRUSTLEDGER</span>
            <span className="hidden sm:inline">•</span>
            <span>AI financial control infrastructure. Verify before money moves.</span>
          </div>

          <div className="flex items-center gap-5 text-[13px]">
            <a href="http://localhost:8000/health" target="_blank" rel="noreferrer" className="hover:text-[#F5F7FA] transition-colors">API</a>
            <Link to="/risk" className="hover:text-[#F5F7FA] transition-colors">Security</Link>
            <Link to="/audit" className="hover:text-[#F5F7FA] transition-colors">Architecture</Link>
            <span className="text-white/20">•</span>
            <span>© 2026 TrustLedger Inc.</span>
          </div>
        </div>
      </footer>

      {/* 4. Command Palette Modal */}
      <CommandPalette isOpen={isCommandOpen} onClose={() => setIsCommandOpen(false)} />
    </div>
  );
};
