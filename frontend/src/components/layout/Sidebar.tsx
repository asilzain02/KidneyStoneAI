import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users as UsersIcon, Image as ImageIcon, Activity, FileText, Settings, LogOut, Shield } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/features/auth/api/authApi';
import { getPermissions } from '@/features/auth/utils/permissions';
import { cn } from '@/utils/cn';

const allNavItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Patients', path: '/patients', icon: UsersIcon },
  { label: 'CT Images', path: '/images', icon: ImageIcon, requirePermission: 'uploadImages' as const },
  { label: 'Diagnoses', path: '/diagnoses', icon: Activity },
  { label: 'Reports', path: '/reports', icon: FileText },
];

export default function Sidebar() {
  const { data: user } = useQuery({
    queryKey: ['profile'],
    queryFn: authApi.getProfile,
  });

  const permissions = getPermissions(user?.role);
  
  const visibleNavItems = allNavItems.filter(item => 
    !item.requirePermission || permissions[item.requirePermission]
  );

  return (
    <div className="flex h-full w-64 flex-col bg-brand-900 text-white">
      <div className="flex h-16 items-center px-6 font-semibold text-lg tracking-wide border-b border-brand-800">
        KidneyStoneAI
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-3">
          {visibleNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-800 text-white'
                    : 'text-brand-100 hover:bg-brand-800/50 hover:text-white'
                )
              }
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="border-t border-brand-800 p-4">
        <nav className="space-y-1">
          {permissions.manageUsers && (
            <NavLink
              to="/users"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors mb-2',
                  isActive
                    ? 'bg-brand-800 text-white'
                    : 'text-brand-100 hover:bg-brand-800/50 hover:text-white'
                )
              }
            >
              <Shield className="h-5 w-5" />
              Users
            </NavLink>
          )}
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-800 text-white'
                  : 'text-brand-100 hover:bg-brand-800/50 hover:text-white'
              )
            }
          >
            <Settings className="h-5 w-5" />
            Settings
          </NavLink>
          <button
            onClick={() => authApi.logout()}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-brand-100 hover:bg-brand-800/50 hover:text-white transition-colors"
          >
            <LogOut className="h-5 w-5" />
            Logout
          </button>
        </nav>
      </div>
    </div>
  );
}
