import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useQuery, useMutation } from '@tanstack/react-query';
import { patientApi } from '@/features/patients/api/patientApi';
import { imageApi } from '../api/imageApi';
import { Upload, X, FileImage, UserPlus } from 'lucide-react';
import toast from 'react-hot-toast';
import { Card, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { formatApiDate } from '@/utils/dateUtils';
import AddPatientModal from '@/features/patients/components/AddPatientModal';
import { authApi } from '@/features/auth/api/authApi';
import { getPermissions } from '@/features/auth/utils/permissions';

export default function CTImages() {
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [imageName, setImageName] = useState('');
  const [isAddingPatient, setIsAddingPatient] = useState(false);

  const { data: patients = [] } = useQuery({
    queryKey: ['patients'],
    queryFn: patientApi.getPatients,
  });

  const { data: user } = useQuery({
    queryKey: ['profile'],
    queryFn: authApi.getProfile,
  });

  const permissions = getPermissions(user?.role);

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!selectedPatientId || !file) throw new Error('Missing file or patient');
      return imageApi.uploadImage(selectedPatientId, file, imageName);
    },
    onSuccess: () => {
      toast.success('Image uploaded successfully');
      setFile(null);
      setImageName('');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to upload image');
    }
  });

  const { data: images = [], refetch: refetchImages } = useQuery({
    queryKey: ['images', selectedPatientId],
    queryFn: () => imageApi.getImagesByPatient(selectedPatientId),
    enabled: !!selectedPatientId,
  });

  const uploadMutationWithRefetch = useMutation({
    mutationFn: async () => { await uploadMutation.mutateAsync(); },
    onSuccess: () => refetchImages()
  });

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.dcm', '.dicom'] },
    maxFiles: 1,
  });

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">CT Images</h1>
        <p className="text-sm text-slate-500 mt-1">
          {permissions.uploadImages 
            ? 'Upload and manage patient CT scans for AI analysis.' 
            : 'View existing patient CT scans.'}
        </p>
      </div>

      {permissions.uploadImages && (
      <Card>
        <CardContent className="p-8 space-y-8">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Select Patient</label>
            <div className="flex gap-4">
              <select
                value={selectedPatientId}
                onChange={(e) => setSelectedPatientId(e.target.value)}
                className="flex-1 rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="" disabled>-- Select a patient --</option>
                {patients.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.firstName} {p.lastName} ({p.patientCode || p.id.split('-')[0]})
                  </option>
                ))}
              </select>
              <Button variant="outline" className="shrink-0 gap-2" onClick={() => setIsAddingPatient(true)}>
                <UserPlus className="h-4 w-4" />
                New Patient
              </Button>
            </div>
          </div>
          
          {isAddingPatient && (
            <AddPatientModal 
              onClose={() => setIsAddingPatient(false)} 
              onSuccess={(id) => {
                setSelectedPatientId(id);
                setIsAddingPatient(false);
              }}
            />
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Image Name (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Kidney CT Scan - Patient 001"
              value={imageName}
              onChange={(e) => setImageName(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 mb-6"
            />
            <label className="block text-sm font-medium text-slate-700 mb-2">CT Image File</label>
            {!file ? (
              <div
                {...getRootProps()}
                className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors cursor-pointer ${
                  isDragActive ? 'border-brand-500 bg-brand-50' : 'border-slate-300 bg-slate-50 hover:bg-slate-100'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className={`h-10 w-10 mb-4 ${isDragActive ? 'text-brand-500' : 'text-slate-400'}`} />
                <p className="text-sm font-medium text-slate-700">Drop CT image here or click to browse</p>
                <p className="text-xs text-slate-500 mt-1">Supports PNG, JPG, DICOM (Max 50MB)</p>
              </div>
            ) : (
              <div className="flex items-center justify-between rounded-xl border border-brand-200 bg-brand-50 p-4">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-100">
                    <FileImage className="h-6 w-6 text-brand-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-800">{file.name}</p>
                    <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <button
                  onClick={() => setFile(null)}
                  className="rounded-full p-2 text-slate-400 hover:bg-brand-100 hover:text-red-500 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            )}
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <Button
              disabled={!file || !selectedPatientId || uploadMutation.isPending}
              onClick={() => uploadMutationWithRefetch.mutate()}
              className="gap-2 px-8"
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload Image'}
            </Button>
          </div>
        </CardContent>
      </Card>
      )}

      {selectedPatientId && (
        <Card>
          <CardContent className="p-0">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 font-medium">Filename</th>
                  <th className="px-6 py-4 font-medium">Upload Date</th>
                  <th className="px-6 py-4 font-medium">Patient</th>
                  <th className="px-6 py-4 font-medium">Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {images.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                      No images found for this patient.
                    </td>
                  </tr>
                ) : (
                  images.map((img) => {
                    const patient = patients.find((p) => p.id === selectedPatientId);
                    return (
                      <tr key={img.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4 font-medium text-slate-800">
                          {img.originalFileName || img.fileName}
                        </td>
                        <td className="px-6 py-4 text-slate-500">
                          {formatApiDate(img.uploadDate)}
                        </td>
                        <td className="px-6 py-4">
                          {patient ? `${patient.firstName} ${patient.lastName}` : 'Unknown'}
                        </td>
                        <td className="px-6 py-4 text-xs font-mono">
                          {img.contentType || 'image/jpeg'} • {(img.fileSize / 1024).toFixed(1)} KB
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
