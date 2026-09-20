import { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Activity, Play, HeartPulse, ShieldCheck, Stethoscope } from 'lucide-react';
import toast from 'react-hot-toast';
import { diagnosisApi } from '../api/diagnosisApi';
import { patientApi } from '@/features/patients/api/patientApi';
import { imageApi } from '@/features/images/api/imageApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { formatApiDate } from '@/utils/dateUtils';
import { getArtifactUrl } from '@/services/artifacts/artifactUrl';
import { CreateDiagnosisRequest, DiagnosisResponse } from '../types';

export default function DiagnosisList() {
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [selectedImageId, setSelectedImageId] = useState('');
  const [currentDiagnosis, setCurrentDiagnosis] = useState<DiagnosisResponse | null>(null);

  const { data: patients = [], isLoading: isLoadingPatients, isError: isErrorPatients } = useQuery({
    queryKey: ['patients'],
    queryFn: patientApi.getPatients,
  });

  const { data: images = [], isLoading: isLoadingImages, isError: isErrorImages } = useQuery({
    queryKey: ['images', selectedPatientId],
    queryFn: () => imageApi.getImagesByPatient(selectedPatientId),
    enabled: !!selectedPatientId
  });

  const runMutation = useMutation({
    mutationFn: (data: CreateDiagnosisRequest) => diagnosisApi.createDiagnosis(data),
    onSuccess: (data) => {
      toast.success('Diagnosis completed');
      setCurrentDiagnosis(data);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.error || 'Unable to start AI analysis. Please try again.';
      toast.error(msg);
    }
  });

  if (isErrorPatients) toast.error('Unable to load patients.');
  if (selectedPatientId && isErrorImages) toast.error('Unable to load CT images.');

  const handlePatientChange = (val: string) => {
    setSelectedPatientId(val);
    setSelectedImageId('');
    setCurrentDiagnosis(null);
  };

  const handleImageChange = (val: string) => {
    setSelectedImageId(val);
    setCurrentDiagnosis(null);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-6">
        <h1 className="text-xl font-bold text-slate-800">Diagnoses</h1>
        <p className="text-sm text-slate-500">Review AI predictions and run new analyses.</p>
      </div>

      <Card className="border-brand-200 shadow-md">
        <CardHeader className="bg-brand-50 border-b border-brand-100">
          <CardTitle className="flex items-center gap-2 text-brand-800">
            <Activity className="h-5 w-5" />
            Run AI Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-slate-700">Select Patient</label>
              <select
                value={selectedPatientId}
                onChange={(e) => handlePatientChange(e.target.value)}
                disabled={isLoadingPatients || runMutation.isPending}
                className="w-full rounded-md border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 bg-white"
              >
                <option value="" disabled>-- Select a patient --</option>
                {patients.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.firstName} {p.lastName} (ID: {p.id.substring(0, 8)})
                  </option>
                ))}
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-slate-700">Select CT Image</label>
              <select
                value={selectedImageId}
                onChange={(e) => handleImageChange(e.target.value)}
                disabled={!selectedPatientId || isLoadingImages || runMutation.isPending}
                className="w-full rounded-md border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:bg-slate-50 bg-white"
              >
                <option value="" disabled>
                  {selectedPatientId 
                    ? (isLoadingImages ? 'Loading images...' : '-- Select image --') 
                    : 'Select a patient first'}
                </option>
                {images.map(img => (
                  <option key={img.id} value={img.id}>
                    {img.originalFileName || img.fileName} — {img.uploadDate ? formatApiDate(img.uploadDate) : 'Date unavailable'}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-6 border-t border-slate-100">
            <Button 
              size="lg"
              className="px-8"
              onClick={() => {
                setCurrentDiagnosis(null);
                runMutation.mutate({ patientId: selectedPatientId, imageId: selectedImageId });
              }}
              disabled={!selectedImageId || runMutation.isPending}
            >
              <Play className="h-4 w-4 mr-2" />
              {runMutation.isPending ? 'Running AI analysis...' : 'Analyze'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {currentDiagnosis && (
        <DiagnosisResultSection 
          diagnosis={currentDiagnosis} 
          patient={patients.find(p => p.id === currentDiagnosis.patientId)} 
        />
      )}
    </div>
  );
}

function DiagnosisResultSection({ diagnosis, patient }: { diagnosis: DiagnosisResponse; patient?: any }) {
  const { data: ctImage } = useQuery({
    queryKey: ['image', diagnosis.imageId],
    queryFn: () => imageApi.getImage(diagnosis.imageId),
    enabled: !!diagnosis.imageId,
  });

  const { data: segBlob } = useQuery({
    queryKey: ['segmentation', diagnosis.id],
    queryFn: () => diagnosisApi.getSegmentationImage(diagnosis.id),
    enabled: !!diagnosis.id && diagnosis.status === 'COMPLETED',
  });

  const { data: gradCamBlob } = useQuery({
    queryKey: ['gradcam', diagnosis.id],
    queryFn: () => diagnosisApi.getGradCamImage(diagnosis.id),
    enabled: !!diagnosis.id && diagnosis.status === 'COMPLETED',
  });

  const segUrl = useMemo(() => {
    if (!segBlob || segBlob.size === 0) return null;
    return URL.createObjectURL(segBlob as Blob);
  }, [segBlob]);

  const gradCamUrl = useMemo(() => {
    if (!gradCamBlob || gradCamBlob.size === 0) return null;
    return URL.createObjectURL(gradCamBlob as Blob);
  }, [gradCamBlob]);

  useEffect(() => {
    return () => {
      if (segUrl) URL.revokeObjectURL(segUrl);
      if (gradCamUrl) URL.revokeObjectURL(gradCamUrl);
    };
  }, [segUrl, gradCamUrl]);

  return (
    <div className="space-y-6 mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Diagnosis Result</h2>
          <div className="text-sm text-slate-500 mt-1 flex flex-col sm:flex-row sm:gap-4">
             <span>Patient: {patient ? `${patient.firstName} ${patient.lastName}` : 'Unknown'}</span>
             <span>Date: {formatApiDate(diagnosis.createdAt)}</span>
             <span>ID: {diagnosis.id.split('-')[0]}</span>
          </div>
        </div>
        <Badge variant={diagnosis.status === 'COMPLETED' ? 'success' : 'error'}>{diagnosis.status}</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex flex-col overflow-hidden">
          <CardHeader className="bg-slate-50 py-3 border-b border-slate-100">
            <CardTitle className="text-sm font-semibold text-slate-700">ORIGINAL CT IMAGE</CardTitle>
          </CardHeader>
          <CardContent className="p-0 flex-1 bg-black flex items-center justify-center min-h-[300px]">
            {ctImage?.url ? (
              <img src={getArtifactUrl(ctImage.url)} alt="Original CT Scanner" className="max-w-full max-h-[350px] object-contain" />
            ) : (
              <span className="text-slate-500 text-sm">Image unavailable</span>
            )}
          </CardContent>
        </Card>

        <Card className="flex flex-col overflow-hidden">
          <CardHeader className="bg-slate-50 py-3 border-b border-slate-100">
            <CardTitle className="text-sm font-semibold text-brand-700">SEGMENTATION RESULT</CardTitle>
          </CardHeader>
          <CardContent className="p-0 flex-1 bg-black flex items-center justify-center min-h-[300px]">
            {segUrl ? (
              <img src={segUrl} alt="AI Segmentation Mask" className="max-w-full max-h-[350px] object-contain" />
            ) : (
              <span className="text-slate-500 text-sm">Artifact unavailable</span>
            )}
          </CardContent>
        </Card>

        <Card className="flex flex-col overflow-hidden">
          <CardHeader className="bg-slate-50 py-3 border-b border-slate-100">
            <CardTitle className="text-sm font-semibold text-purple-700">CLASSIFICATION / GRAD-CAM RESULT</CardTitle>
          </CardHeader>
          <CardContent className="p-0 flex-1 bg-black flex items-center justify-center min-h-[300px]">
            {gradCamUrl ? (
              <img src={gradCamUrl} alt="Grad-CAM Overlay" className="max-w-full max-h-[350px] object-contain" />
            ) : (
              <span className="text-slate-500 text-sm">Artifact unavailable</span>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-5 flex flex-col h-full justify-center">
            <div className="text-sm font-semibold text-brand-600 uppercase tracking-wide mb-1">Prediction</div>
            <div className="text-2xl font-bold text-slate-800">{diagnosis.predictedClass || '—'}</div>
            <div className="text-sm font-medium text-slate-500 mt-2">
              Confidence: {diagnosis.confidence ? `${(diagnosis.confidence * 100).toFixed(1)}%` : '—'}
            </div>
          </CardContent>
        </Card>

        <Card className={diagnosis.consistencyStatus === 'DISAGREEMENT' ? 'border-red-200 bg-red-50/30' : diagnosis.consistencyStatus === 'CONSISTENT' ? 'border-green-200 bg-green-50/30' : ''}>
          <CardContent className="p-5 flex flex-col h-full justify-between">
            <div className="flex items-center gap-2 mb-2 text-slate-600">
              <ShieldCheck className="h-4 w-4" />
              <h4 className="font-semibold text-sm uppercase tracking-wide">Consistency</h4>
            </div>
            <div className="font-bold uppercase text-slate-800 mb-2">
              {diagnosis.consistencyStatus || 'UNKNOWN'}
            </div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-[200px]">
              {diagnosis.consistencyMessage || 'Cross-validation analysis result.'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex flex-col h-full justify-between">
             <div className="flex items-center gap-2 mb-2 text-amber-600">
              <HeartPulse className="h-4 w-4" />
              <h4 className="font-semibold text-sm uppercase tracking-wide">Severity</h4>
            </div>
            <div className="font-bold text-slate-800 mb-2">{diagnosis.severityLevel || '—'}</div>
            <p className="text-xs text-slate-500 leading-relaxed">
              {diagnosis.severityReason || 'Severity assessment details.'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex flex-col h-full justify-between">
             <div className="flex items-center gap-2 mb-2 text-green-600">
              <Stethoscope className="h-4 w-4" />
              <h4 className="font-semibold text-sm uppercase tracking-wide">Treatment</h4>
            </div>
            <div className="font-bold text-slate-800 line-clamp-1 mb-2">{diagnosis.treatmentCategory || '—'}</div>
            <p className="text-xs text-slate-500 leading-relaxed">
              {diagnosis.treatmentRecommendation || 'Clinical recommendations.'}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
