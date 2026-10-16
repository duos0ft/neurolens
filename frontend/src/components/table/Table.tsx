import type { Key, ReactNode } from "react";

import { Button } from "../button";
import { cn } from "../../lib/cn";
import { tableStyles as styles } from "./Table.styles";

export interface TableColumn<T> {
    key: string;
    title: string;
    render: (row: T) => ReactNode;
    className?: string;
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
    loading?: boolean;
    emptyMessage?: string;
    pagination?: TablePagination;
}

export function Table<T>({
    columns,
    rows,
    rowKey,
    loading = false,
    emptyMessage = "No records found.",
    pagination,
}: TableProps<T>) {
    const showPaginationControls = pagination && pagination.totalPages > 1;

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
                                    className={cn(styles.headCell, column.className)}
                                >
                                    {column.title}
                                </th>
                            ))}
                        </tr>
                    </thead>

                    <tbody aria-busy={loading}>
                        {loading ? (
                            <tr>
                                <td colSpan={columns.length} className={styles.empty}>
                                    Loading...
                                </td>
                            </tr>
                        ) : rows.length === 0 ? (
                            <tr>
                                <td colSpan={columns.length} className={styles.empty}>
                                    {emptyMessage}
                                </td>
                            </tr>
                        ) : (
                            rows.map((row) => (
                                <tr key={rowKey(row)} className={styles.row}>
                                    {columns.map((column) => (
                                        <td
                                            key={column.key}
                                            className={cn(styles.cell, column.className)}
                                        >
                                            {column.render(row)}
                                        </td>
                                    ))}
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
                                onClick={() => pagination.onPageChange(pagination.page - 1)}
                            >
                                Previous
                            </Button>

                            <Button
                                variant="secondary"
                                size="sm"
                                disabled={loading || pagination.page >= pagination.totalPages}
                                onClick={() => pagination.onPageChange(pagination.page + 1)}
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
