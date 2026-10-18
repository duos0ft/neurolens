import type { Key, ReactNode } from "react";

import { Button } from "../button";
import { DropdownMenu } from "../dropdown-menu/DropdownMenu";
import { cn } from "../../lib/cn";
import { tableStyles as styles } from "./Table.styles";

export interface TableColumn<T> {
    key: string;
    title: string;
    render: (row: T) => ReactNode;
    className?: string;
}

export interface TableRowAction<T> {
    label: string;
    onSelect: (row: T) => void;
    hidden?: (row: T) => boolean;
    disabled?: (row: T) => boolean;
    destructive?: boolean;
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
    loading?: boolean;
    emptyMessage?: string;
    pagination?: TablePagination;
}

export function Table<T>({
    columns,
    rows,
    rowKey,
    rowActions = [],
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
                            rows.map((row) => {
                                const availableActions = rowActions.filter(
                                    (action) => !action.hidden?.(row),
                                );

                                return (
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
                                                {availableActions.length > 0 && (
                                                    <DropdownMenu
                                                        label="Row actions"
                                                        items={availableActions.map(
                                                            (action) => ({
                                                                label: action.label,
                                                                destructive: action.destructive,
                                                                disabled: action.disabled?.(row),
                                                                onSelect: () => action.onSelect(row),
                                                            }),
                                                        )}
                                                    />
                                                )}
                                            </td>
                                        )}
                                    </tr>
                                );
                            })
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
