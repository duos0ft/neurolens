export type EmployeeRole = "admin" | "employee";

export type EmployeeStatus = "active" | "suspended";

export interface AuthenticatedEmployee {
    id: string;
    role: EmployeeRole;
    status: EmployeeStatus;
}
