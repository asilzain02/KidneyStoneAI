import { useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { diagnosisApi } from '../api/diagnosisApi';
import { patientApi } from '@/features/patients/api/patientApi';
import { imageApi } from '@/features/images/api/imageApi';
import { getArtifactUrl } from '@/services/artifacts/artifactUrl';
import { PageLoader } from '@/components/common/Loader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Activity, HeartPulse, User, Clock, ShieldCheck, Stethoscope } from 'lucide-react';
import { formatApiDate } from '@/utils/dateUtils';

export default function DiagnosisResult() {
  const { id } = useParams<{ id: string }>();

  const { data: diagnosis, isLoading: isLoadingDiag, error } = useQuery({
    queryKey: ['diagnosis', id],
    queryFn: () => diagnosisApi.getDiagnosis(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll every 2 seconds if processing
      const status = query.state.data?.status;
      if (status === 'PENDING' || status === 'PROCESSING') return 2000;
      return false;
    }
  });

  const { data: patient } = useQuery({
    queryKey: ['patient', diagnosis?.patientId],
    queryFn: () => patientApi.getPatient(diagnosis!.patientId),
    enabled: !!diagnosis?.patientId,
  });

  const { data: ctImage } = useQuery({
    queryKey: ['image', diagnosis?.imageId],
    queryFn: () => imageApi.getImage(diagnosis!.imageId),
    enabled: !!diagnosis?.imageId,
  });

  const { data: comparisonBlob } = useQuery({
    queryKey: ['comparison', diagnosis?.id],
    queryFn: () => diagnosisApi.getComparisonImage(diagnosis!.id),
    enabled: !!diagnosis?.id && diagnosis.status === 'COMPLETED',
  });

  const comparisonImageUrl = useMemo(() => {
    if (!comparisonBlob) return null;
    return URL.createObjectURL(comparisonBlob as Blob);
  }, [comparisonBlob]);

  // Clean up object URL when component unmounts or blob changes
  useEffect(() => {
    return () => {
      if (comparisonImageUrl) {
        URL.revokeObjectURL(comparisonImageUrl);
      }
    };
  }, [comparisonImageUrl]);

  if (isLoadingDiag) return <PageLoader />;
  if (error || !diagnosis) return <div className="p-8 text-center text-red-500">Failed to load diagnosis results.</div>;

  const isProcessing = diagnosis.status === 'PENDING' || diagnosis.status === 'PROCESSING';
  const isFailed = diagnosis.status === 'FAILED';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between bg-white p-6 rounded-xl border border-slate-200 shadow-sm gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            Diagnosis Result
            <Badge variant={
              diagnosis.status === 'COMPLETED' ? 'success' : 
              (diagnosis.status === 'FAILED' ? 'error' : 'warning')
            }>
              {diagnosis.status}
            </Badge>
          </h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
            <span className="flex items-center gap-1"><User className="h-4 w-4" /> {patient?.firstName} {patient?.lastName}</span>
            <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> {formatApiDate(diagnosis.createdAt)}</span>
            <span className="font-mono text-xs bg-slate-100 px-2 py-0.5 rounded">ID: {diagnosis.id.split('-')[0]}</span>
          </div>
        </div>
      </div>

      {isProcessing && (
        <Card className="border-brand-200 bg-brand-50">
          <CardContent className="p-12 flex flex-col items-center justify-center text-center">
            <Activity className="h-12 w-12 text-brand-600 animate-pulse mb-4" />
            <h3 className="text-lg font-semibold text-brand-900">Running diagnosis...</h3>
            <p className="text-sm text-brand-700 mt-2">Analyzing CT image using classification and segmentation models.</p>
          </CardContent>
        </Card>
      )}

      {isFailed && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-8 text-center">
            <h3 className="text-lg font-semibold text-red-700">Diagnosis Processing Failed</h3>
            <p className="text-sm text-red-600 mt-1">An error occurred during AI analysis. Please try again or contact support.</p>
          </CardContent>
        </Card>
      )}

      {diagnosis.status === 'COMPLETED' && (
        <>
          {/* Main Visualization Area */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Panel 1: Original CT */}
            <Card className="flex flex-col overflow-hidden">
              <CardHeader className="bg-slate-50 py-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2 text-slate-700">
                  <div className="h-2 w-2 rounded-full bg-slate-400" />
                  ORIGINAL CT IMAGE
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0 flex-1 bg-black flex items-center justify-center min-h-[300px]">
                {ctImage?.url ? (
                   <img 
                    src={getArtifactUrl(ctImage.url)} 
                    alt="Original CT Scan" 
                    className="max-w-full max-h-[500px] object-contain"
                  />
                ) : (
                  <span className="text-slate-500 text-sm">Image unavailable</span>
                )}
              </CardContent>
              <div className="bg-white p-3 border-t border-slate-100 text-xs text-slate-500">
                Patient Upload
              </div>
            </Card>

            {/* Panel 2: AI Comparison Visualization from Backend */}
            <Card className="flex flex-col overflow-hidden">
              <CardHeader className="bg-slate-50 py-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2 text-brand-700">
                  <div className="h-2 w-2 rounded-full bg-brand-500" />
                  AI COMPARISON VISUALIZATION
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0 flex-1 bg-black flex items-center justify-center min-h-[300px] relative">
                {comparisonImageUrl ? (
                   <img 
                    src={comparisonImageUrl} 
                    alt="AI Comparison Visualization" 
                    className="max-w-full max-h-[500px] object-contain"
                  />
                ) : (
                  <span className="text-slate-500 text-sm">Generating comparison...</span>
                )}
              </CardContent>
              <div className="bg-white p-3 border-t border-slate-100 flex justify-between items-center text-xs">
                <span className="text-slate-600 font-medium">AUTHORITATIVE AI ANALYSIS</span>
              </div>
            </Card>

          </div>

          {/* Details Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            
            {/* Classification */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center gap-2 text-brand-600 mb-2">
                  <Activity className="h-4 w-4" />
                  <h4 className="font-semibold text-sm uppercase tracking-wide">Prediction</h4>
                </div>
                <div className="text-3xl font-bold text-slate-800 mb-1">{diagnosis.predictedClass || '—'}</div>
                <div className="text-sm font-medium text-slate-500">
                  Confidence: <span className="text-brand-600">{diagnosis.confidence ? `${(diagnosis.confidence * 100).toFixed(1)}%` : '—'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Consistency */}
            <Card className={
              diagnosis.consistencyStatus === 'DISAGREEMENT' ? 'border-red-200 bg-red-50/30' : 
              diagnosis.consistencyStatus === 'CONSISTENT' ? 'border-green-200 bg-green-50/30' : ''
            }>
              <CardContent className="p-5 flex flex-col h-full justify-between">
                <div>
                  <div className={`flex items-center gap-2 mb-2 ${
                    diagnosis.consistencyStatus === 'DISAGREEMENT' ? 'text-red-600' : 'text-slate-600'
                  }`}>
                    <ShieldCheck className="h-4 w-4" />
                    <h4 className="font-semibold text-sm uppercase tracking-wide">Consistency</h4>
                  </div>
                  <div className={`font-bold uppercase ${
                    diagnosis.consistencyStatus === 'DISAGREEMENT' ? 'text-red-700' : 
                    diagnosis.consistencyStatus === 'CONSISTENT' ? 'text-green-700' : 'text-amber-600'
                  }`}>
                    {diagnosis.consistencyStatus || 'UNKNOWN'}
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                  {diagnosis.consistencyMessage || 'Cross-validation analysis result.'}
                </p>
              </CardContent>
            </Card>

            {/* Severity */}
            <Card>
              <CardContent className="p-5 flex flex-col h-full justify-between">
                <div>
                  <div className="flex items-center gap-2 text-amber-600 mb-2">
                    <HeartPulse className="h-4 w-4" />
                    <h4 className="font-semibold text-sm uppercase tracking-wide">Severity</h4>
                  </div>
                  <div className="font-bold text-slate-800">{diagnosis.severityLevel || '—'}</div>
                </div>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed line-clamp-2">
                  {diagnosis.severityReason || 'Severity assessment details.'}
                </p>
              </CardContent>
            </Card>

            {/* Treatment */}
            <Card>
              <CardContent className="p-5 flex flex-col h-full justify-between">
                <div>
                  <div className="flex items-center gap-2 text-green-600 mb-2">
                    <Stethoscope className="h-4 w-4" />
                    <h4 className="font-semibold text-sm uppercase tracking-wide">Treatment</h4>
                  </div>
                  <div className="font-bold text-slate-800 line-clamp-1">{diagnosis.treatmentCategory || '—'}</div>
                </div>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed line-clamp-2">
                  {diagnosis.treatmentRecommendation || 'Clinical recommendations.'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Tech Metadata */}
          <div className="text-center">
            <p className="text-xs text-slate-400">
              Pipeline: {diagnosis.classificationModel} | {diagnosis.segmentationModel} • Inference Time: {diagnosis.processingTimeMs}ms ({diagnosis.device})
            </p>
          </div>
        </>
      )}

      {/* Disclaimer */}
      <div className="bg-slate-100 p-4 rounded-xl text-center border border-slate-200 mt-8">
        <p className="text-sm font-medium text-slate-600">
          Clinical decision support only. Results should be reviewed alongside clinical findings by a qualified healthcare professional.
        </p>
      </div>
    </div>
  );
}
