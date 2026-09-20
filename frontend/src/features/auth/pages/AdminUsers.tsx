import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api/authApi';
import { Card, CardContent } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { PageLoader } from '@/components/common/Loader';
import { Plus, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function AdminUsers() {
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [userToDelete, setUserToDelete] = useState<string | null>(null);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin_users'],
    queryFn: authApi.getUsers,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => authApi.deleteUser(id),
    onSuccess: () => {
      toast.success('User deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['admin_users'] });
      setUserToDelete(null);
    },
    onError: () => {
      toast.error('Unable to delete user');
      setUserToDelete(null);
    }
  });

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-800">User Management</h1>
          <p className="text-sm text-slate-500">Admin view to control system access and roles.</p>
        </div>
        <Button onClick={() => setIsAdding(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add User
        </Button>
      </div>

      {isAdding && (
        <CreateUserForm onCancel={() => setIsAdding(false)} />
      )}

      {userToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
           <Card className="max-w-md w-full shadow-lg border-0 shadow-lg">
             <CardContent className="p-6">
               <h3 className="text-lg font-bold text-slate-900 mb-2">Delete this user?</h3>
               <p className="text-sm text-slate-600 mb-6">Are you sure you want to delete this account? This action cannot be undone and will revoke all access immediately.</p>
               <div className="flex justify-end gap-3">
                 <Button variant="ghost" onClick={() => setUserToDelete(null)}>Cancel</Button>
                 <Button variant="danger" onClick={() => deleteMutation.mutate(userToDelete)}>
                   {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                 </Button>
               </div>
             </CardContent>
           </Card>
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-medium">Name</th>
                <th className="px-6 py-4 font-medium">Email</th>
                <th className="px-6 py-4 font-medium">Role</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                    No users found.
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-800">
                      {user.firstName} {user.lastName}
                    </td>
                    <td className="px-6 py-4">{user.email}</td>
                    <td className="px-6 py-4">
                      {user.role && (
                        <Badge variant={user.role === 'ROLE_ADMIN' ? 'error' : (user.role === 'ROLE_DOCTOR' ? 'success' : 'neutral')} className="mr-2">
                          {user.role.replace('ROLE_', '')}
                        </Badge>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant={user.status === 'ACTIVE' ? 'success' : 'neutral'}>
                        {user.status || 'ACTIVE'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-right">
                       <Button 
                         variant="ghost" 
                         size="sm" 
                         className="text-red-500 hover:text-red-700 hover:bg-red-50"
                         onClick={() => setUserToDelete(user.id)}
                       >
                         <Trash2 className="h-4 w-4" />
                       </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function CreateUserForm({ onCancel }: { onCancel: () => void }) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    username: '',
    password: '',
    role: 'DOCTOR',
    phone: ''
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => authApi.createUser(data),
    onSuccess: () => {
      toast.success('User created successfully');
      queryClient.invalidateQueries({ queryKey: ['admin_users'] });
      onCancel();
    },
    onError: (error: any) => {
      const msg = error.response?.data?.error?.details || 'Unable to create user';
      toast.error(msg);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.firstName || !formData.email || !formData.password || !formData.username) {
      toast.error('Required fields are missing');
      return;
    }
    createMutation.mutate(formData);
  };

  return (
    <Card className="border-brand-200 shadow-md mb-6">
      <CardContent className="p-6">
        <h2 className="text-lg font-bold text-slate-800 mb-4">Create New Account</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-700 mb-1">First Name *</label>
              <input 
                type="text" 
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500" 
                value={formData.firstName}
                onChange={e => setFormData({...formData, firstName: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Last Name</label>
              <input 
                type="text" 
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500" 
                value={formData.lastName}
                onChange={e => setFormData({...formData, lastName: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Email *</label>
              <input 
                type="email" 
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500" 
                value={formData.email}
                onChange={e => setFormData({...formData, email: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Username *</label>
              <input 
                type="text" 
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500" 
                value={formData.username}
                onChange={e => setFormData({...formData, username: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Password *</label>
              <input 
                type="password" 
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500" 
                value={formData.password}
                onChange={e => setFormData({...formData, password: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Role *</label>
              <select 
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 bg-white"
                value={formData.role}
                onChange={e => setFormData({...formData, role: e.target.value})}
              >
                <option value="DOCTOR">DOCTOR</option>
                <option value="ADMIN">ADMIN</option>
                <option value="PATIENT">PATIENT</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
