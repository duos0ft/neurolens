import { useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { Avatar } from "../../../components/avatar";
import { Button } from "../../../components/button";
import { Filters } from "../../../components/filters/Filters";
import type { FilterDefinition, FilterValues } from "../../../components/filters/Filters.types";
import { PageHeader } from "../../../components/page-header/PageHeader";
import { Table, type TableColumn } from "../../../components/table/Table";
import { getEmployees } from "../../../lib/employees";
import type { Employee, EmployeeRole, EmployeeStatus, PageResponse } from "../../../types/employee";
import { InviteEmployeeDialog } from "./InviteEmployeeDialog";
import { employeesPageStyles as styles } from "./EmployeesPage.styles";

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
            <span className={styles.role}>{employee.role}</span>
        ),
    },
    {
        key: "status",
        title: "Status",
        render: (employee) => (
            <span className={`${styles.status} ${statusStyles[employee.status]}`}>
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
    const [ employees, setEmployees ] = useState<PageResponse<Employee> | null>(null);
    const [ filters, setFilters ] = useState<FilterValues>({
        search: "",
        status: null,
        roles: [],
    });

    const [ inviteOpen, setInviteOpen ] = useState(false);
    const [ refreshKey, setRefreshKey ] = useState(0);
    const [ page, setPage ] = useState(1);
    const [ loading, setLoading ] = useState(true);
    const [ error, setError ] = useState<string | null>(null);

    const search = typeof filters.search === "string" ? filters.search : "";
    const status = filters.status as EmployeeStatus | null;
    const roles = filters.roles;

    useEffect(() => {
        let cancelled = false;

        async function loadEmployees() {
            setLoading(true);
            setError(null);

            try {
                const result = await getEmployees({
                    page,
                    pageSize: PAGE_SIZE,
                    search,
                    status: status ?? undefined,
                    roles: Array.isArray(roles) ? roles as EmployeeRole[] : [],
                });

                if (!cancelled) {
                    setEmployees(result);
                }
            } catch {
                if (!cancelled) {
                    setError("Unable to load employees. Please try again.");
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        void loadEmployees();

        return () => {
            cancelled = true;
        };
    }, [ page, search, status, roles, refreshKey ]);

    function updateFilters(nextFilters: FilterValues) {
        setFilters(nextFilters);
        setPage(1);
    }

    return (
        <div className={styles.root}>
            <PageHeader
                title="Employees"
                description="View and manage employees in your organization."
                actions={
                    <Button variant="primary" onClick={() => setInviteOpen(true)}>
                        <Plus aria-hidden="true"/>
                        Invite employee
                    </Button>
                }
            />

            <section className={styles.directory} aria-label="Employee directory">
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
                onInvited={() => {
                    setPage(1);
                    setRefreshKey((current) => current + 1);
                }}
            />
        </div>
    );
}
