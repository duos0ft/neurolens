import { useEffect, useState } from "react";

import { Avatar } from "../../../components/avatar";
import { Filters } from "../../../components/filters/Filters";
import type { FilterDefinition, FilterValues } from "../../../components/filters/Filters.types";
import { Table, type TableColumn } from "../../../components/table/Table";
import { getEmployees } from "../../../lib/employees";
import type { Employee, EmployeeRole, EmployeeStatus, PageResponse } from "../../../types/employee";
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
        key: "role",
        type: "select",
        placeholder: "All roles",
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
        role: null,
    });

    const [ page, setPage ] = useState(1);
    const [ loading, setLoading ] = useState(true);
    const [ error, setError ] = useState<string | null>(null);

    const search = typeof filters.search === "string" ? filters.search : "";
    const status = filters.status as EmployeeStatus | null;
    const role = filters.role as EmployeeRole | null;

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
                    role: role ?? undefined,
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
    }, [ page, search, status, role ]);

    function updateFilters(nextFilters: FilterValues) {
        setFilters(nextFilters);
        setPage(1);
    }

    return (
        <div className={styles.root}>
            <header className={styles.pageHeader}>
                <div>
                    <h1 className={styles.title}>Employees</h1>
                    <p className={styles.description}>
                        View and manage employees in your organization.
                    </p>
                </div>
            </header>

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
        </div>
    );
}
