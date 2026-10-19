import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Avatar } from "../../../components/avatar";
import { Button } from "../../../components/button";
import { ConfirmationDialog } from "../../../components/dialog/ConfirmationDialog";
import { Filters } from "../../../components/filters/Filters";
import type { FilterDefinition, FilterValues } from "../../../components/filters/Filters.types";
import { PageHeader } from "../../../components/page-header/PageHeader";
import { Table, type TableColumn, type TableRowAction } from "../../../components/table/Table";
import { getEmployees, reactivateEmployee, suspendEmployee } from "../../../lib/employees";
import { useAuth } from "../../../providers/AuthProvider";
import type { Employee, EmployeeRole, EmployeeStatus } from "../../../types/employee";

import { employeesPageStyles as styles } from "./EmployeesPage.styles";
import { InviteEmployeeDialog } from "./InviteEmployeeDialog";

const PAGE_SIZE = 20;

type EmployeeAction = "suspend" | "reactivate";

interface SelectedEmployeeAction {
    employee: Employee;
    type: EmployeeAction;
}

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
        render: (employee) => (
            <span
                className={`${styles.status} ${statusStyles[employee.status]}`}
            >
                {statusLabels[employee.status]}
            </span>
        ),
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

    const [ selectedAction, setSelectedAction ] =
        useState<SelectedEmployeeAction | null>(null);

    const search = typeof filters.search === "string"
        ? filters.search
        : "";

    const status = filters.status as EmployeeStatus | null;

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
                roles: [ ...selectedRoles ].sort(),
            },
        ],
        queryFn: () => getEmployees({
            page,
            pageSize: PAGE_SIZE,
            search,
            status: status ?? undefined,
            roles: selectedRoles,
        }),
        placeholderData: keepPreviousData,
    });

    const employees = employeesQuery.data;
    const loading = employeesQuery.isPending;

    const error = employeesQuery.isError
        ? "Unable to load employees. Please try again."
        : null;

    const statusMutation = useMutation({
        mutationFn: async (action: SelectedEmployeeAction) => {
            if (action.type === "suspend") {
                await suspendEmployee(action.employee.id);
            } else {
                await reactivateEmployee(action.employee.id);
            }
        },
        onSuccess: async (_, action) => {
            setSelectedAction(null);

            await queryClient.invalidateQueries({
                queryKey: [ "employees" ],
            });

            toast.success(
                action.type === "suspend"
                    ? "Employee suspended successfully."
                    : "Employee reactivated successfully.",
            );
        },
        onError: () => {
            toast.error(
                "Unable to update employee status. Please try again.",
            );
        },
    });

    const rowActions: TableRowAction<Employee>[] = [
        {
            label: "Suspend employee",
            destructive: true,
            hidden: (employee) => employee.status !== "active",
            disabled: (employee) => (
                employee.id === currentEmployee?.id
                || statusMutation.isPending
            ),
            onSelect: (employee) => {
                setSelectedAction({
                    employee,
                    type: "suspend",
                });
            },
        },
        {
            label: "Reactivate employee",
            hidden: (employee) => employee.status !== "suspended",
            disabled: () => statusMutation.isPending,
            onSelect: (employee) => {
                setSelectedAction({
                    employee,
                    type: "reactivate",
                });
            },
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

    function closeConfirmation() {
        if (!statusMutation.isPending) {
            setSelectedAction(null);
        }
    }

    function confirmAction() {
        if (!selectedAction || statusMutation.isPending) {
            return;
        }

        statusMutation.mutate(selectedAction);
    }

    const isSuspending = selectedAction?.type === "suspend";

    const selectedEmployeeName =
        selectedAction?.employee.displayName
        || selectedAction?.employee.email
        || "this employee";

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

            <ConfirmationDialog
                open={selectedAction !== null}
                onClose={closeConfirmation}
                onConfirm={confirmAction}
                loading={statusMutation.isPending}
                destructive={isSuspending}
                title={
                    isSuspending
                        ? "Suspend employee"
                        : "Reactivate employee"
                }
                confirmLabel={
                    isSuspending
                        ? "Suspend employee"
                        : "Reactivate employee"
                }
                description={
                    isSuspending
                        ? `Are you sure you want to suspend ${selectedEmployeeName}? They will immediately lose access to NeuroLens, and all active sessions will be revoked.`
                        : `Are you sure you want to reactivate ${selectedEmployeeName}? They will regain access to NeuroLens and must sign in again.`
                }
            />
        </div>
    );
}
