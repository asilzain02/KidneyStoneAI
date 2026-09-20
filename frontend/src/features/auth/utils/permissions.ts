export type Role = 'ADMIN' | 'ROLE_ADMIN' | 'DOCTOR' | 'ROLE_DOCTOR' | 'PATIENT' | 'ROLE_PATIENT';

export interface RolePermissions {
  manageUsers: boolean;
  uploadImages: boolean;
  managePatients: boolean;
  viewDiagnoses: boolean;
  viewReports: boolean;
}

const rolePermissionsConfig: Record<string, RolePermissions> = {
  ADMIN: {
    manageUsers: true,
    uploadImages: true,
    managePatients: true,
    viewDiagnoses: true,
    viewReports: true,
  },
  DOCTOR: {
    manageUsers: false,
    uploadImages: false,
    managePatients: true,
    viewDiagnoses: true,
    viewReports: true,
  },
  PATIENT: {
    manageUsers: false,
    uploadImages: false,
    managePatients: false,
    viewDiagnoses: false,
    viewReports: false,
  }
};

export function getPermissions(role?: string): RolePermissions {
  if (!role) return rolePermissionsConfig.PATIENT;
  const normalizedRole = role.replace('ROLE_', '').toUpperCase();
  return rolePermissionsConfig[normalizedRole] || rolePermissionsConfig.PATIENT;
}

export function hasPermission(role: string | undefined, permission: keyof RolePermissions): boolean {
  const permissions = getPermissions(role);
  return permissions[permission] === true;
}
