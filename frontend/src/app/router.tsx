import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import Login from '@/features/auth/pages/Login';
import Dashboard from '@/features/dashboard/pages/Dashboard';
import Patients from '@/features/patients/pages/Patients';
import PatientDetails from '@/features/patients/pages/PatientDetails';
import CTImages from '@/features/images/pages/CTImages';
import DiagnosisList from '@/features/diagnoses/pages/DiagnosisList';
import DiagnosisResult from '@/features/diagnoses/pages/DiagnosisResult';
import Reports from '@/features/reports/pages/Reports';
import RouteError from '@/components/common/RouteError';
import Settings from '@/features/settings/pages/Settings';
import AdminUsers from '@/features/auth/pages/AdminUsers';

// Simple exact Auth guard
function RequireAuth() {
  const token = localStorage.getItem('accessToken');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

// We will replace these with actual page imports as we create them
const Placeholder = ({ title }: { title: string }) => <div className="p-8"><h1>{title}</h1></div>;

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    element: <RequireAuth />,
    children: [
      {
        path: '/',
        element: <AppShell />,
        errorElement: <RouteError />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: 'dashboard', element: <Dashboard /> },
          { path: 'patients', element: <Patients /> },
          { path: 'patients/:id', element: <PatientDetails /> },
          { path: 'images', element: <CTImages /> },
          { path: 'diagnoses', element: <DiagnosisList /> },
          { path: 'diagnoses/:id', element: <DiagnosisResult /> },
          { path: 'reports', element: <Reports /> },
          { path: 'reports/:id', element: <Placeholder title="Report Detail" /> },
          { path: 'settings', element: <Settings /> },
          { path: 'users', element: <AdminUsers /> }
        ],
      }
    ]
  }
]);
