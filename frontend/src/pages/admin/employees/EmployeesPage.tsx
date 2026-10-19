import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Avatar } from "../../../components/avatar";
import { Button } from "../../../components/button";
import { Filters } from "../../../components/filters/Filters";
import type { FilterDefinition, FilterValues } from "../../../components/filters/Filters.types";
import { PageHeader } from "../../../components/page-header/PageHeader";
import { Table, type TableColumn, type TableRowAction } from "../../../components/table/Table";
import { getEmployees, reactivateEmployee, revokeEmployeeInvitation, suspendEmployee } from "../../../lib/employees";
import { useAuth } from "../../../providers/AuthProvider";
import type { Employee, EmployeeRole, EmployeeStatus } from "../../../types/employee";

import { employeesPageStyles as styles } from "./EmployeesPage.styles";
import { InviteEmployeeDialog } from "./InviteEmployeeDialog";

const PAGE_SIZE = 20;

const employeeFilters: FilterDefinition[] = [
    {
        key: "search",
        type: "search",
        placeholder: "Search employees...",
        debounceMs: 300,
    },
    {
        key: "status",
        type: "segmentedControl",
        label: "Filter employees by status",
        options: [
            { label: "All", value: null },
            { label: "Active", value: "active" },
            { label: "Invited", value: "invited" },
            { label: "Suspended", value: "suspended" },
            { label: "Archived", value: "archived" },
        ],
    },
    {
        key: "roles",
        type: "checkboxGroup",
        label: "Role",
        options: [
            { label: "Admin", value: "admin" },
            { label: "Employee", value: "employee" },
        ],
    },
];

const statusLabels: Record<EmployeeStatus, string> = {
    active: "Active",
    invited: "Invited",
    suspended: "Suspended",
};

const statusStyles: Record<EmployeeStatus, string> = {
    active: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
    invited: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
    suspended: "bg-red-500/10 text-red-700 dark:text-red-400",
};

const columns: TableColumn<Employee>[] = [
    {
        key: "name",
        title: "Name",
        render: (employee) => (
            <div className={styles.employeeCell}>
                <Avatar
                    name={employee.displayName || employee.email || "Employee"}
                    size="sm"
                />

                <span className={styles.employeeName}>
                    {employee.displayName || "Unnamed employee"}
                </span>
            </div>
        ),
    },
    {
        key: "email",
        title: "Email",
        render: (employee) => (
            <span className={styles.employeeEmail}>
                {employee.email || "No email"}
            </span>
        ),
    },
    {
        key: "role",
        title: "Role",
        render: (employee) => (
            <span className={styles.role}>
                {employee.role}
            </span>
        ),
    },

    {
        key: "status",
        title: "Status",
        render: (employee) => {
            const invitationRevoked =
                employee.status === "invited"
                && employee.invitationStatus === "cancelled";

            const label = invitationRevoked
                ? "Invitation revoked"
                : statusLabels[employee.status];

            const className = invitationRevoked
                ? "bg-muted text-fg-muted"
                : statusStyles[employee.status];

            return (
                <span className={`${styles.status} ${className}`}>
                    {label}
                </span>
            );
        },
    },

    {
        key: "createdAt",
        title: "Joined",
        render: (employee) => (
            <span className={styles.date}>
                {new Date(employee.createdAt).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                })}
            </span>
        ),
    },
];

export function Component() {
    const queryClient = useQueryClient();
    const { employee: currentEmployee } = useAuth();

    const [ filters, setFilters ] = useState<FilterValues>({
        search: "",
        status: null,
        roles: [],
    });

    const [ page, setPage ] = useState(1);
    const [ inviteOpen, setInviteOpen ] = useState(false);

    const search = typeof filters.search === "string"
        ? filters.search
        : "";

    const selectedStatus = filters.status;

    const directory = selectedStatus === "archived"
        ? "archived"
        : "current";

    const status = selectedStatus === "archived"
        ? undefined
        : selectedStatus as EmployeeStatus | null;

    const selectedRoles: EmployeeRole[] = Array.isArray(filters.roles)
        ? filters.roles as EmployeeRole[]
        : [];

    const employeesQuery = useQuery({
        queryKey: [
            "employees",
            {
                page,
                pageSize: PAGE_SIZE,
                search,
                status,
                directory,
                roles: [ ...selectedRoles ].sort(),
            },
        ],
        queryFn: () => getEmployees({
            page,
            pageSize: PAGE_SIZE,
            search,
            status: status ?? undefined,
            directory,
            roles: selectedRoles,
        }),
        placeholderData: keepPreviousData,
    });

    const employees = employeesQuery.data;
    const loading = employeesQuery.isPending;

    const error = employeesQuery.isError
        ? "Unable to load employees. Please try again."
        : null;

    const rowActions: TableRowAction<Employee>[] = [
        {
            label: "Suspend employee",
            destructive: true,
            hidden: (employee) => employee.status !== "active",
            disabled: (employee) => employee.id === currentEmployee?.id,
            confirmation: {
                title: "Suspend employee",
                description: (employee) =>
                    `Suspend ${employee.displayName || employee.email || "this employee"}? Their access will be blocked and all active sessions revoked.`,
                confirmLabel: "Suspend employee",
            },
            onSelect: (employee) => suspendEmployee(employee.id),
        },
        {
            label: "Reactivate employee",
            hidden: (employee) => employee.status !== "suspended",
            confirmation: {
                title: "Reactivate employee",
                description: (employee) =>
                    `Reactivate ${employee.displayName || employee.email || "this employee"}? They will regain access to NeuroLens but must sign in again.`,
                confirmLabel: "Reactivate employee",
            },
            onSelect: (employee) => reactivateEmployee(employee.id),
        },
        {
            label: "Revoke invitation",
            destructive: true,
            hidden: (employee) => (
                employee.status !== "invited"
                || ![
                    "ready",
                    "pending",
                    "failed",
                    "expired",
                ].includes(employee.invitationStatus ?? "")
            ),
            confirmation: {
                title: "Revoke invitation",
                description: (employee) =>
                    `Revoke the invitation for ${employee.displayName || employee.email || "this employee"}? Their invitation link will become invalid and they won't be able to complete onboarding.`,
                confirmLabel: "Revoke invitation",
            },
            onSelect: (employee) => revokeEmployeeInvitation(employee.id),
        },
    ];

    function updateFilters(nextFilters: FilterValues) {
        setFilters(nextFilters);
        setPage(1);
    }

    function handleInvitationCreated() {
        setPage(1);

        void queryClient.invalidateQueries({
            queryKey: [ "employees" ],
        });
    }

    async function handleRowActionSuccess(
        _employee: Employee,
        action: TableRowAction<Employee>,
    ) {
        await queryClient.invalidateQueries({
            queryKey: [ "employees" ],
        });

        const messages: Record<string, string> = {
            "Suspend employee": "Employee suspended successfully.",
            "Reactivate employee": "Employee reactivated successfully.",
            "Revoke invitation": "Invitation revoked successfully.",
        };

        toast.success(
            messages[action.label] ?? "Action completed successfully.",
        );
    }

    return (
        <div className={styles.root}>
            <PageHeader
                title="Employees"
                description="View and manage employees in your organization."
                actions={
                    <Button
                        variant="primary"
                        onClick={() => setInviteOpen(true)}
                    >
                        <Plus aria-hidden="true"/>
                        Invite employee
                    </Button>
                }
            />

            <section
                className={styles.directory}
                aria-label="Employee directory"
            >
                <div className={styles.toolbar}>
                    <Filters
                        definitions={employeeFilters}
                        values={filters}
                        onChange={updateFilters}
                    />
                </div>

                {error ? (
                    <div className={styles.error} role="alert">
                        {error}
                    </div>
                ) : (
                    <Table
                        columns={columns}
                        rows={employees?.items ?? []}
                        rowKey={(employee) => employee.id}
                        rowActions={rowActions}
                        onRowActionSuccess={handleRowActionSuccess}
                        loading={loading}
                        emptyMessage="No employees found. Try adjusting your search or filters."
                        pagination={
                            employees
                                ? {
                                    page: employees.page,
                                    pageSize: employees.pageSize,
                                    totalItems: employees.totalItems,
                                    totalPages: employees.totalPages,
                                    onPageChange: setPage,
                                }
                                : undefined
                        }
                    />
                )}
            </section>

            <InviteEmployeeDialog
                open={inviteOpen}
                onClose={() => setInviteOpen(false)}
                onInvited={handleInvitationCreated}
            />
        </div>
    );
}
