export interface Patient {
  id: string; // UUID
  patientCode: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string; // LocalDate
  gender: string;
  bloodGroup: string;
  phone: string;
  email: string;
  address: string;
  status: string;
  createdAt: string;
}

export interface CreatePatientRequest {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: string;
  bloodGroup?: string;
  phone?: string;
  email?: string;
  address?: string;
}
