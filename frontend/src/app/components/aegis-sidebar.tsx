import { Shield, Activity, Network, Ban } from 'lucide-react';
import { Link, useLocation } from 'react-router';

export function AegisSidebar() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Sessions', icon: Activity },
    { path: '/network', label: 'Network', icon: Network },
    { path: '/tools', label: 'Tools', icon: Ban },
  ];

  return (
    <div
      className="group/sidebar relative h-screen bg-[#0f1419] border-r border-[#1e293b] flex flex-col transition-[width] duration-200 ease-in-out w-12 hover:w-56 overflow-hidden flex-shrink-0"
    >
      {/* Header */}
      <div className="p-3 border-b border-[#1e293b] flex items-center gap-3 min-w-0">
        <Shield className="w-5 h-5 text-[#3b82f6] flex-shrink-0" />
        <div className="opacity-0 group-hover/sidebar:opacity-100 transition-opacity duration-150 whitespace-nowrap overflow-hidden">
          <div className="text-[14px] tracking-wide leading-tight">AEGIS</div>
          <div className="text-[10px] text-[#94a3b8] uppercase tracking-wide">Guardrail Runtime</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2">
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                title={item.label}
                className={`
                  flex items-center gap-3 px-2 py-2 rounded text-[13px] transition-colors min-w-0
                  ${isActive
                    ? 'bg-[#1e293b] text-[#e4e7eb]'
                    : 'text-[#94a3b8] hover:bg-[#1e293b]/50 hover:text-[#e4e7eb]'
                  }
                `}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="opacity-0 group-hover/sidebar:opacity-100 transition-opacity duration-150 whitespace-nowrap overflow-hidden">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-2 border-t border-[#1e293b]">
        <div className="opacity-0 group-hover/sidebar:opacity-100 transition-opacity duration-150 text-[11px] text-[#94a3b8] whitespace-nowrap overflow-hidden px-1">
          <div className="flex justify-between mb-1">
            <span>Status</span>
            <span className="text-[#10b981]">Active</span>
          </div>
          <div className="flex justify-between">
            <span>Uptime</span>
            <span>99.9%</span>
          </div>
        </div>
        <div className="group-hover/sidebar:hidden flex justify-center py-1">
          <div className="w-1.5 h-1.5 rounded-full bg-[#10b981]" />
        </div>
      </div>
    </div>
  );
}
