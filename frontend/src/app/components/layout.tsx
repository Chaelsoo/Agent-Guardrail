import { Outlet } from 'react-router';
import { AegisSidebar } from './aegis-sidebar';

export function Layout() {
  return (
    <div className="flex h-screen bg-[#0a0e1a] text-[#e4e7eb]">
      <AegisSidebar />
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}
