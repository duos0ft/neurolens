import type { Key, ReactNode } from "react";

import { Button } from "../button";
import { cn } from "../../lib/cn";

import { TableRowActions } from "./TableRowActions";
import { tableStyles as styles } from "./Table.styles";

export interface TableColumn<T> {
    key: string;
    title: string;
    render: (row: T) => ReactNode;
    className?: string;
}

export interface TableRowActionConfirmation<T> {
    title: string;
    description: string | ((row: T) => string);
    confirmLabel: string;
}

export interface TableRowAction<T> {
    label: string;
    onSelect: (row: T) => void | Promise<void>;
    hidden?: (row: T) => boolean;
    disabled?: (row: T) => boolean;
    destructive?: boolean;
    confirmation?: TableRowActionConfirmation<T>;
}

export interface TablePagination {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
    onPageChange: (page: number) => void;
}

export interface TableProps<T> {
    columns: TableColumn<T>[];
    rows: T[];
    rowKey: (row: T) => Key;
    rowActions?: TableRowAction<T>[];
    onRowActionSuccess?: (
        row: T,
        action: TableRowAction<T>,
    ) => void | Promise<void>;
    onRowActionError?: (
        error: unknown,
        row: T,
        action: TableRowAction<T>,
    ) => void;
    loading?: boolean;
    emptyMessage?: string;
    pagination?: TablePagination;
}

export function Table<T>({
    columns,
    rows,
    rowKey,
    rowActions = [],
    onRowActionSuccess,
    onRowActionError,
    loading = false,
    emptyMessage = "No records found.",
    pagination,
}: TableProps<T>) {
    const hasRowActions = rowActions.length > 0;
    const columnCount = columns.length + (hasRowActions ? 1 : 0);

    const showPaginationControls = Boolean(
        pagination && pagination.totalPages > 1,
    );

    return (
        <div className={styles.root}>
            <div className={styles.overflow}>
                <table className={styles.table}>
                    <thead className={styles.header}>
                        <tr>
                            {columns.map((column) => (
                                <th
                                    key={column.key}
                                    scope="col"
                                    className={cn(
                                        styles.headCell,
                                        column.className,
                                    )}
                                >
                                    {column.title}
                                </th>
                            ))}

                            {hasRowActions && (
                                <th
                                    scope="col"
                                    className={cn(
                                        styles.headCell,
                                        "w-14 text-right",
                                    )}
                                >
                                    <span className="sr-only">
                                        Actions
                                    </span>
                                </th>
                            )}
                        </tr>
                    </thead>

                    <tbody aria-busy={loading}>
                        {loading ? (
                            <tr>
                                <td
                                    colSpan={columnCount}
                                    className={styles.empty}
                                >
                                    Loading...
                                </td>
                            </tr>
                        ) : rows.length === 0 ? (
                            <tr>
                                <td
                                    colSpan={columnCount}
                                    className={styles.empty}
                                >
                                    {emptyMessage}
                                </td>
                            </tr>
                        ) : (
                            rows.map((row) => (
                                <tr
                                    key={rowKey(row)}
                                    className={styles.row}
                                >
                                    {columns.map((column) => (
                                        <td
                                            key={column.key}
                                            className={cn(
                                                styles.cell,
                                                column.className,
                                            )}
                                        >
                                            {column.render(row)}
                                        </td>
                                    ))}

                                    {hasRowActions && (
                                        <td
                                            className={cn(
                                                styles.cell,
                                                "w-14 text-right",
                                            )}
                                        >
                                            <TableRowActions
                                                row={row}
                                                actions={rowActions}
                                                onSuccess={onRowActionSuccess}
                                                onError={onRowActionError}
                                            />
                                        </td>
                                    )}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {pagination && (
                <div className={styles.pagination}>
                    <span className={styles.paginationText}>
                        {pagination.totalItems === 0
                            ? "No records"
                            : `Showing ${(pagination.page - 1) * pagination.pageSize + 1}–${Math.min(
                                pagination.page * pagination.pageSize,
                                pagination.totalItems,
                            )} of ${pagination.totalItems}`}
                    </span>

                    {showPaginationControls && (
                        <div className={styles.paginationActions}>
                            <Button
                                variant="secondary"
                                size="sm"
                                disabled={loading || pagination.page <= 1}
                                onClick={() => pagination.onPageChange(
                                    pagination.page - 1,
                                )}
                            >
                                Previous
                            </Button>

                            <Button
                                variant="secondary"
                                size="sm"
                                disabled={
                                    loading
                                    || pagination.page >= pagination.totalPages
                                }
                                onClick={() => pagination.onPageChange(
                                    pagination.page + 1,
                                )}
                            >
                                Next
                            </Button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
