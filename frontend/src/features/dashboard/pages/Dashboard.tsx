import { useQuery } from '@tanstack/react-query';
import { patientApi } from '@/features/patients/api/patientApi';
import { diagnosisApi } from '@/features/diagnoses/api/diagnosisApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { PageLoader } from '@/components/common/Loader';
import { Activity, Users, Clock, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { data: patients = [], isLoading: isLoadingPatients } = useQuery({
    queryKey: ['patients'],
    queryFn: patientApi.getPatients,
  });

  const { data: diagnoses = [], isLoading: isLoadingDiagnoses } = useQuery({
    queryKey: ['diagnoses'],
    queryFn: diagnosisApi.getDiagnoses,
  });

  if (isLoadingPatients || isLoadingDiagnoses) {
    return <PageLoader />;
  }

  // Handle both Array defaults and Spring Boot Page<T> response objects
  const patientList = Array.isArray(patients) ? patients : (patients as any).content || [];
  const diagnosisList = Array.isArray(diagnoses) ? diagnoses : (diagnoses as any).content || [];

  const latestDiagnoses = [...diagnosisList].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()).slice(0, 5);
  const totalPatients = (patients as any).totalElements ?? patientList.length;
  const totalDiagnoses = (diagnoses as any).totalElements ?? diagnosisList.length;
  const pendingDiagnoses = diagnosisList.filter((d: any) => d.status === 'PENDING' || d.status === 'PROCESSING').length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">Overview of recent clinical activity and system status.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Patients" value={totalPatients.toString()} icon={Users} />
        <StatCard title="Total Diagnoses" value={totalDiagnoses.toString()} icon={Activity} />
        <StatCard title="Pending Cases" value={pendingDiagnoses.toString()} icon={Clock} />
        <StatCard title="System Alerts" value="0" icon={AlertTriangle} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Diagnoses</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3 font-medium">Patient</th>
                    <th className="px-6 py-3 font-medium">Prediction</th>
                    <th className="px-6 py-3 font-medium">Confidence</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {latestDiagnoses.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                        No recent diagnoses found.
                      </td>
                    </tr>
                  ) : (
                    latestDiagnoses.map((diag) => {
                      const patient = patientList.find((p: any) => p.id === diag.patientId);
                      return (
                        <tr key={diag.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 font-medium text-slate-800">
                            {patient ? `${patient.firstName} ${patient.lastName}` : 'Unknown'}
                          </td>
                          <td className="px-6 py-4">
                            {diag.predictedClass || '—'}
                          </td>
                          <td className="px-6 py-4">
                            {diag.confidence ? `${(diag.confidence * 100).toFixed(1)}%` : '—'}
                          </td>
                          <td className="px-6 py-4">
                            <Badge variant={diag.status === 'COMPLETED' ? 'success' : 'warning'}>
                              {diag.status}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 text-slate-500">
                            {new Date(diag.createdAt).toLocaleDateString()}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
            {latestDiagnoses.length > 0 && (
              <div className="border-t border-slate-100 p-4 bg-slate-50 text-center">
                <Link to="/diagnoses" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                  View all diagnoses →
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-sm">
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <span className="text-slate-500">API Gateway</span>
                <Badge variant="success">Online</Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <span className="text-slate-500">AI Engine</span>
                <Badge variant="success">Online</Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-slate-100">
                <span className="text-slate-500">Storage</span>
                <span className="font-medium text-slate-700">Healthy</span>
              </div>
              <div className="p-4 bg-brand-50 rounded-lg text-brand-800 mt-4">
                <p className="font-medium mb-1">Clinical Standard Active</p>
                <p className="text-xs text-brand-600">Decision support features enabled for radiologist review workflow.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon }: { title: string, value: string, icon: any }) {
  return (
    <Card>
      <CardContent className="p-6 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">{value}</p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50">
          <Icon className="h-6 w-6 text-brand-600" />
        </div>
      </CardContent>
    </Card>
  );
}
