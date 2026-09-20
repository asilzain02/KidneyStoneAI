import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { patientApi } from '../api/patientApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { PageLoader } from '@/components/common/Loader';
import { ArrowLeft, User, Phone, Mail, MapPin, Calendar, Activity, Droplet } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { formatApiDate } from '@/utils/dateUtils';

export default function PatientDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: patient, isLoading, isError } = useQuery({
    queryKey: ['patient', id],
    queryFn: () => patientApi.getPatient(id!),
    enabled: !!id,
  });

  if (isLoading) return <PageLoader />;

  if (isError || !patient) {
    return (
      <div className="text-center p-8">
        <h2 className="text-xl font-bold text-slate-800">Unable to load patient</h2>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/patients')}>
          Return to Patients
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" className="p-2" onClick={() => navigate('/patients')}>
          <ArrowLeft className="h-5 w-5 text-slate-500" />
        </Button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800">
              {patient.firstName} {patient.lastName}
            </h1>
            <Badge variant={patient.status === 'ACTIVE' ? 'success' : 'neutral'}>
              {patient.status}
            </Badge>
          </div>
          <p className="text-sm text-slate-500 flex items-center gap-2 mt-1">
            <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-xs">
              {patient.patientCode}
            </span>
            Added {formatApiDate(patient.createdAt)}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="bg-slate-50 border-b border-slate-100">
            <CardTitle className="flex items-center gap-2 text-brand-800">
              <User className="h-5 w-5" />
              Personal Information
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-y-4 gap-x-2">
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1 flex items-center gap-1">
                  <Calendar className="h-3 w-3" /> Date of Birth
                </p>
                <p className="text-sm text-slate-800 font-medium">{patient.dateOfBirth}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1 flex items-center gap-1">
                  <User className="h-3 w-3" /> Gender
                </p>
                <p className="text-sm text-slate-800 font-medium capitalize">{patient.gender.toLowerCase()}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1 flex items-center gap-1">
                  <Droplet className="h-3 w-3" /> Blood Group
                </p>
                <p className="text-sm text-slate-800 font-medium">{patient.bloodGroup || 'Not specified'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="bg-slate-50 border-b border-slate-100">
            <CardTitle className="flex items-center gap-2 text-brand-800">
              <Activity className="h-5 w-5" />
              Contact Details
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="space-y-4">
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1 flex items-center gap-1">
                  <Phone className="h-3 w-3" /> Phone Number
                </p>
                <p className="text-sm text-slate-800 font-medium">{patient.phone || 'Not provided'}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1 flex items-center gap-1">
                  <Mail className="h-3 w-3" /> Email Address
                </p>
                <p className="text-sm text-slate-800 font-medium">{patient.email || 'Not provided'}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1 flex items-center gap-1">
                  <MapPin className="h-3 w-3" /> Address
                </p>
                <p className="text-sm text-slate-800 font-medium">{patient.address || 'Not provided'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
