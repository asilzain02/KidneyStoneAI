import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import { patientApi } from '../api/patientApi';
import { Card, CardContent } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { PageLoader } from '@/components/common/Loader';
import AddPatientModal from '../components/AddPatientModal';

export default function Patients() {
  const [isAdding, setIsAdding] = useState(false);
  const navigate = useNavigate();

  const { data: patients = [], isLoading } = useQuery({
    queryKey: ['patients'],
    queryFn: patientApi.getPatients,
  });

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-800">Patients</h1>
          <p className="text-sm text-slate-500">Manage patient records and clinical history.</p>
        </div>
        <Button onClick={() => setIsAdding(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Patient
        </Button>
      </div>

      {isAdding && <AddPatientModal onClose={() => setIsAdding(false)} />}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-medium">Patient Code</th>
                <th className="px-6 py-4 font-medium">Name</th>
                <th className="px-6 py-4 font-medium">DOB</th>
                <th className="px-6 py-4 font-medium">Gender</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {patients.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                    No patients found.
                  </td>
                </tr>
              ) : (
                patients.map((patient) => (
                  <tr key={patient.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs">{patient.patientCode || patient.id.split('-')[0]}</td>
                    <td className="px-6 py-4 font-medium text-slate-800">
                      {patient.firstName} {patient.lastName}
                    </td>
                    <td className="px-6 py-4">{patient.dateOfBirth}</td>
                    <td className="px-6 py-4 capitalize">{patient.gender?.toLowerCase() || '—'}</td>
                    <td className="px-6 py-4">
                      <Badge variant={patient.status === 'ACTIVE' ? 'success' : 'neutral'}>
                        {patient.status || 'ACTIVE'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button variant="ghost" size="sm" className="text-brand-600" onClick={() => navigate(`/patients/${patient.id}`)}>
                        View Profile
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
