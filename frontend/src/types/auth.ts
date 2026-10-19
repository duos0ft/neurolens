export enum EmployeeRole {
    Admin = "admin",
    Employee = "employee",
}

export enum EmployeeStatus {
    Invited = "invited",
    Active = "active",
    Suspended = "suspended",
}

export interface AuthenticatedEmployee {
    id: string;
    email: string | null;
    role: EmployeeRole;
    status: EmployeeStatus;
    display_name: string | null;
    job_title: string | null;
    department: string | null;
    team: string | null;
}
