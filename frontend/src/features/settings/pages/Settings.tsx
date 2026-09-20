import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/features/auth/api/authApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { User, Shield, Key } from 'lucide-react';
import { PageLoader } from '@/components/common/Loader';

export default function Settings() {
  const { data: user, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: authApi.getProfile
  });

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">Manage your account and application preferences.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-brand-500" />
                Profile Information
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-slate-500 font-medium">Name</p>
                  <p className="text-slate-800">{user?.firstName} {user?.lastName}</p>
                </div>
                <div>
                  <p className="text-slate-500 font-medium">Email</p>
                  <p className="text-slate-800">{user?.email}</p>
                </div>
                <div>
                  <p className="text-slate-500 font-medium">Username</p>
                  <p className="text-slate-800">{user?.username}</p>
                </div>
                {user?.phone && (
                  <div>
                    <p className="text-slate-500 font-medium">Phone</p>
                    <p className="text-slate-800">{user?.phone}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader className="border-b border-slate-100 bg-slate-50">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Shield className="h-4 w-4 text-slate-500" />
                Security
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-4 text-sm">
              <div>
                <p className="text-slate-500 font-medium">Role</p>
                <div className="mt-1 flex flex-wrap gap-2">
                  {user?.role && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-brand-100 text-brand-800">
                      {user.role}
                    </span>
                  )}
                </div>
              </div>
              <div className="pt-2 border-t border-slate-100">
                <button className="flex items-center gap-2 text-brand-600 hover:text-brand-700 font-medium transition-colors">
                  <Key className="h-4 w-4" />
                  Change Password
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
