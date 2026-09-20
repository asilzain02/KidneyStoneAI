import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportApi } from '../api/reportApi';
import { patientApi } from '@/features/patients/api/patientApi';
import { diagnosisApi } from '@/features/diagnoses/api/diagnosisApi';
import { imageApi } from '@/features/images/api/imageApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { FileText, Download, Activity, ExternalLink, Image as ImageIcon } from 'lucide-react';
import toast from 'react-hot-toast';
import { formatApiDate } from '@/utils/dateUtils';

// Helper component for loading authenticated blobs
const AuthenticatedImage = ({ 
  fetchFn, 
  id, 
  title, 
  fallbackMsg 
}: { 
  fetchFn: (id: string) => Promise<Blob>, 
  id: string, 
  title: string, 
  fallbackMsg: string 
}) => {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let objectUrl: string;
    
    if (id) {
      setError(false);
      fetchFn(id)
        .then(blob => {
          objectUrl = window.URL.createObjectURL(blob);
          setUrl(objectUrl);
        })
        .catch(() => {
          setError(true);
        });
    }

    return () => {
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [id, fetchFn]);

  return (
    <div className="flex flex-col border border-slate-200 rounded-lg overflow-hidden h-full bg-white shadow-sm">
      <div className="bg-slate-50 py-2 border-b border-slate-200 px-3 flex items-center gap-2">
        <ImageIcon className="h-4 w-4 text-brand-600" />
        <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">{title}</h3>
      </div>
      <div className="flex-grow flex items-center justify-center p-4 bg-slate-100 min-h-[250px]">
        {error ? (
           <p className="text-sm font-medium text-slate-500">{fallbackMsg}</p>
        ) : url ? (
           <img src={url} alt={title} className="max-w-full max-h-[300px] object-contain shadow-sm rounded border border-slate-200 bg-white" />
        ) : (
           <div className="animate-pulse rounded-md bg-slate-200 h-full w-full"></div>
        )}
      </div>
    </div>
  );
};

export default function Reports() {
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [selectedDiagnosisId, setSelectedDiagnosisId] = useState('');
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);

  const { data: patients = [], isLoading: isLoadingPatients, isError: isErrorPatients } = useQuery({
    queryKey: ['patients'],
    queryFn: patientApi.getPatients,
  });

  const { data: diagnoses = [], isLoading: isLoadingDiagnoses, isError: isErrorDiagnoses } = useQuery({
    queryKey: ['diagnoses'],
    queryFn: diagnosisApi.getDiagnoses,
  });

  const patientDiagnoses = diagnoses.filter(d => d.patientId === selectedPatientId && d.status === 'COMPLETED');
  const activeDiagnosis = diagnoses.find(d => d.id === selectedDiagnosisId);
  const activePatient = patients.find(p => p.id === selectedPatientId);

  const { isLoading: isLoadingReportDetail } = useQuery({
    queryKey: ['reportDetail', selectedDiagnosisId],
    queryFn: () => reportApi.getReportDetail(selectedDiagnosisId),
    enabled: !!selectedDiagnosisId
  });

  if (isErrorPatients) toast.error('Unable to load patients.');
  if (selectedPatientId && isErrorDiagnoses) toast.error('Unable to load diagnoses.');

  const downloadPdf = async (viewOnly: boolean = false) => {
    if (!activeDiagnosis || !activePatient) return;
    try {
      setIsGeneratingPdf(true);
      const blob = await reportApi.getReportPdf(activeDiagnosis.id);
      
      const objectUrl = window.URL.createObjectURL(blob);
      
      if (viewOnly) {
         window.open(objectUrl, '_blank');
      } else {
         const a = document.createElement('a');
         a.href = objectUrl;
         a.download = `KidneyStoneAI_Report_${activePatient.firstName}_${activePatient.lastName}_${activeDiagnosis.id.substring(0,8)}.pdf`;
         document.body.appendChild(a);
         a.click();
         document.body.removeChild(a);
         toast.success('PDF download complete');
      }
      
      // We don't revoke immediately when viewing, as modern browsers need the URL alive 
      if (!viewOnly) {
         setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000);
      }
    } catch {
      toast.error('Unable to generate clinical report');
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-6">
        <h1 className="text-xl font-bold text-slate-800">Clinical Reports</h1>
        <p className="text-sm text-slate-500">Access and generate authoritative PDF clinical decision-support reports.</p>
      </div>

      <Card className="border-brand-200 shadow-md">
        <CardHeader className="bg-brand-50 border-b border-brand-100">
          <CardTitle className="flex items-center gap-2 text-brand-800">
            <FileText className="h-5 w-5" />
            Report Selection
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-slate-700">Select Patient</label>
              <select
                value={selectedPatientId}
                onChange={(e) => { setSelectedPatientId(e.target.value); setSelectedDiagnosisId(''); }}
                disabled={isLoadingPatients}
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
              <label className="block text-sm font-semibold text-slate-700">Select Diagnosis</label>
              <select
                value={selectedDiagnosisId}
                onChange={(e) => setSelectedDiagnosisId(e.target.value)}
                disabled={!selectedPatientId || isLoadingDiagnoses}
                className="w-full rounded-md border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:bg-slate-50 bg-white"
              >
                <option value="" disabled>
                  {selectedPatientId 
                    ? (isLoadingDiagnoses ? 'Loading diagnoses...' : '-- Select diagnosis --') 
                    : 'Select a patient first'}
                </option>
                {patientDiagnoses.map(diag => (
                  <option key={diag.id} value={diag.id}>
                    {diag.predictedClass || 'Result'} — {diag.createdAt ? formatApiDate(diag.createdAt) : 'Date unavailable'}
                  </option>
                ))}
              </select>
              {selectedPatientId && !isLoadingDiagnoses && patientDiagnoses.length === 0 && (
                <p className="text-xs text-amber-600 mt-2 font-medium">No completed diagnoses available for this patient.</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {selectedDiagnosisId && activeDiagnosis && activePatient && (
        <Card className="border-slate-200 mt-8 shadow-sm">
          <CardHeader className="bg-slate-50 py-4 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
              <Activity className="h-4 w-4 text-brand-600" />
              Clinical Report Preview
            </CardTitle>
            <div className="flex items-center gap-3">
              <Button 
                size="sm" 
                variant="outline" 
                onClick={() => downloadPdf(true)} 
                disabled={isGeneratingPdf || isLoadingReportDetail}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View Report
              </Button>
              <Button 
                size="sm" 
                variant="primary" 
                onClick={() => downloadPdf(false)} 
                disabled={isGeneratingPdf || isLoadingReportDetail}
              >
                <Download className="h-4 w-4 mr-2" />
                Download PDF
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
             {isLoadingReportDetail ? (
                <div className="p-12 text-center text-slate-500 text-sm animate-pulse">Loading clinical details...</div>
             ) : (
                <>
                  <div className="p-6 md:p-8 bg-white text-sm text-slate-700">
                     <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 pb-6 border-b border-slate-200">
                        <div>
                          <span className="text-slate-400 block text-xs uppercase tracking-wider mb-1">Patient Information</span>
                          <span className="font-semibold text-slate-800 block text-base">{activePatient.firstName} {activePatient.lastName}</span>
                          <span className="text-slate-500 block text-xs mt-1">ID: {activePatient.id.substring(0,8)}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-xs uppercase tracking-wider mb-1">Diagnosis Information</span>
                          <span className="font-semibold text-slate-800 block text-base">{activeDiagnosis.predictedClass || 'Unknown'}</span>
                          <span className="text-slate-500 block text-xs mt-1">Date: {formatApiDate(activeDiagnosis.createdAt)}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-xs uppercase tracking-wider mb-1">Clinical Assessment</span>
                          <span className="font-medium text-amber-700 block line-clamp-1" title={activeDiagnosis.severityLevel}>{activeDiagnosis.severityLevel || 'Not assessed'}</span>
                          <span className="text-slate-500 block text-xs mt-1 line-clamp-1" title={activeDiagnosis.severityReason}>{activeDiagnosis.severityReason || '-'}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-xs uppercase tracking-wider mb-1">AI Prediction Confidence</span>
                          <span className="font-bold text-brand-700 text-xl block">{(activeDiagnosis.confidence * 100).toFixed(1)}%</span>
                        </div>
                     </div>
                     
                     <div className="bg-slate-50 p-4 rounded-md border border-slate-200 mb-8">
                       <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Treatment Protocol</h3>
                       <p className="font-medium text-slate-800 mb-1">{activeDiagnosis.treatmentCategory || 'N/A'}</p>
                       <p className="text-slate-600 text-sm">{activeDiagnosis.treatmentRecommendation || 'No recommendation available.'}</p>
                     </div>

                     <div className="mb-4">
                       <h3 className="text-sm font-bold text-slate-700 uppercase tracking-widest border-b border-slate-200 pb-2">AI Visual Analysis</h3>
                     </div>

                     <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <AuthenticatedImage 
                          fetchFn={imageApi.downloadImage} 
                          id={activeDiagnosis.imageId} 
                          title="Original CT" 
                          fallbackMsg="Original CT image unavailable" 
                        />
                        <AuthenticatedImage 
                          fetchFn={diagnosisApi.getSegmentationImage} 
                          id={activeDiagnosis.id} 
                          title="Segmentation" 
                          fallbackMsg="Segmentation visualization unavailable" 
                        />
                        <AuthenticatedImage 
                          fetchFn={diagnosisApi.getGradCamImage} 
                          id={activeDiagnosis.id} 
                          title="Grad-CAM Classification" 
                          fallbackMsg="Grad-CAM visualization unavailable" 
                        />
                     </div>
                  </div>
                </>
             )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
