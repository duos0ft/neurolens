import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "../../components/button";
import { ConfirmationDialog } from "../../components/dialog/ConfirmationDialog";
import { PageHeader } from "../../components/page-header/PageHeader";
import { Select } from "../../components/select/Select";
import {
    archiveTask,
    createTask,
    deleteTask,
    getTask,
    getTasks,
    getTaskStats,
    restoreTask,
    type SavedTask,
    type TaskInput,
    type TaskSortBy,
    type TaskStatus,
    updateSubtaskCompletion,
    updateTask,
    updateTaskStatus,
} from "../../lib/tasks";
import { TaskEditorDialog } from "./TaskEditorDialog";
import { TaskListItem } from "./TaskListsItem";
import { tasksPageStyles as styles } from "./TasksPage.styles";
import { useLocation, useNavigate } from "react-router";

type TaskFilter = "all" | TaskStatus | "archived";

const PAGE_SIZE = 20;

const filters: { label: string; value: TaskFilter }[] = [
    { label: "All", value: "all" },
    { label: "To do", value: "todo" },
    { label: "In progress", value: "in_progress" },
    { label: "Completed", value: "completed" },
    { label: "Archived", value: "archived" },
];

const sortOptions: { label: string; value: TaskSortBy }[] = [
    { label: "Date created", value: "created_at" },
    { label: "Last updated", value: "updated_at" },
    { label: "Due date", value: "due_date" },
    { label: "Priority", value: "priority" },
];

export function Component() {
    const location = useLocation();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const linkedTaskId = (
        location.state as { taskId?: unknown } | null
    )?.taskId;

    const taskId = typeof linkedTaskId === "string"
    && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(linkedTaskId)
        ? linkedTaskId
        : null;

    const [ filter, setFilter ] = useState<TaskFilter>("all");
    const [ page, setPage ] = useState(1);
    const [ sortBy, setSortBy ] = useState<TaskSortBy>("created_at");

    const [ editorOpen, setEditorOpen ] = useState(false);
    const [ editingTask, setEditingTask ] = useState<SavedTask | null>(null);
    const [ deletingTask, setDeletingTask ] = useState<SavedTask | null>(null);

    const linkedTaskQuery = useQuery({
        queryKey: [ "tasks", "detail", taskId ],
        queryFn: () => getTask(taskId!),
        enabled: taskId !== null,
        retry: false,
    });

    const tasksQuery = useQuery({
        queryKey: [ "tasks", "list", filter, page, sortBy ],
        queryFn: () => getTasks({
            page,
            page_size: PAGE_SIZE,
            status: filter === "all" || filter === "archived"
                ? undefined
                : filter,
            archived: filter === "archived",
            sort_by: sortBy,
            sort_order: "desc",
        }),
    });

    const statsQuery = useQuery({
        queryKey: [ "tasks", "stats" ],
        queryFn: getTaskStats,
    });

    const tasks = tasksQuery.data?.items ?? [];
    const totalItems = tasksQuery.data?.total_items ?? 0;
    const totalPages = tasksQuery.data?.total_pages ?? 0;

    const statusMutation = useMutation({
        mutationFn: ({
            taskId,
            status,
        }: {
            taskId: string;
            status: TaskStatus;
        }) => updateTaskStatus(taskId, status),

        onSuccess: () => {
            void queryClient.invalidateQueries({
                queryKey: [ "tasks" ],
            });

            toast.success("Task status updated");
        },

        onError: (error) => {
            toast.error("Unable to update task", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const taskEditorMutation = useMutation({
        mutationFn: ({
            task,
            values,
        }: {
            task: SavedTask | null;
            values: TaskInput;
        }) => task
            ? updateTask(task.id, values)
            : createTask(values),

        onSuccess: (_savedTask, variables) => {
            void queryClient.invalidateQueries({
                queryKey: [ "tasks" ],
            });

            setEditorOpen(false);
            setEditingTask(null);

            if (!variables.task) {
                setFilter("all");
                setPage(1);
                setSortBy("created_at");
            }

            toast.success(
                variables.task
                    ? "Task updated"
                    : "Task created",
            );
        },

        onError: (error) => {
            toast.error("Unable to save task", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const archiveMutation = useMutation({
        mutationFn: archiveTask,

        onSuccess: () => {
            setPage(1);

            void queryClient.invalidateQueries({
                queryKey: [ "tasks" ],
            });

            toast.success("Task archived");
        },

        onError: (error) => {
            toast.error("Unable to archive task", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const restoreMutation = useMutation({
        mutationFn: restoreTask,

        onSuccess: () => {
            setPage(1);

            void queryClient.invalidateQueries({
                queryKey: [ "tasks" ],
            });

            toast.success("Task restored");
        },

        onError: (error) => {
            toast.error("Unable to restore task", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: deleteTask,

        onSuccess: () => {
            setDeletingTask(null);
            setPage(1);

            void queryClient.invalidateQueries({
                queryKey: [ "tasks" ],
            });

            toast.success("Task deleted");
        },

        onError: (error) => {
            toast.error("Unable to delete task", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const subtaskMutation = useMutation({
        mutationFn: ({
            taskId,
            subtaskId,
            completed,
        }: {
            taskId: string;
            subtaskId: string;
            completed: boolean;
        }) => updateSubtaskCompletion(
            taskId,
            subtaskId,
            completed,
        ),

        onSuccess: () => {
            void queryClient.invalidateQueries({
                queryKey: [ "tasks" ],
            });
        },

        onError: (error) => {
            toast.error("Unable to update subtask", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const actionsPending =
        statusMutation.isPending
        || taskEditorMutation.isPending
        || archiveMutation.isPending
        || restoreMutation.isPending
        || deleteMutation.isPending
        || subtaskMutation.isPending;

    function handleStatusChange(
        taskId: string,
        status: TaskStatus,
    ) {
        if (actionsPending) {
            return;
        }

        statusMutation.mutate({
            taskId,
            status,
        });
    }

    function handleFilterChange(value: TaskFilter) {
        setFilter(value);
        setPage(1);
    }

    function handleSortChange(value: TaskSortBy) {
        setSortBy(value);
        setPage(1);
    }

    function handleCreateTask() {
        if (actionsPending) {
            return;
        }

        setEditingTask(null);
        setEditorOpen(true);
    }

    function handleEditTask(task: SavedTask) {
        if (actionsPending || task.archived_at !== null) {
            return;
        }

        setEditingTask(task);
        setEditorOpen(true);
    }

    function handleCloseEditor() {
        if (taskEditorMutation.isPending) {
            return;
        }

        setEditorOpen(false);
        setEditingTask(null);
    }

    function handleArchiveTask(taskId: string) {
        if (actionsPending) {
            return;
        }

        archiveMutation.mutate(taskId);
    }

    function handleRestoreTask(taskId: string) {
        if (actionsPending) {
            return;
        }

        restoreMutation.mutate(taskId);
    }

    function handleDeleteTask(task: SavedTask) {
        if (actionsPending) {
            return;
        }

        setDeletingTask(task);
    }

    function handleCloseDeleteDialog() {
        if (deleteMutation.isPending) {
            return;
        }

        setDeletingTask(null);
    }

    function handleConfirmDelete() {
        if (!deletingTask || actionsPending) {
            return;
        }

        deleteMutation.mutate(deletingTask.id);
    }

    useEffect(() => {
        if (!taskId) {
            return;
        }

        if (linkedTaskQuery.isSuccess) {
            setEditingTask(linkedTaskQuery.data);
            setEditorOpen(true);

            void navigate(
                location.pathname,
                {
                    replace: true,
                    state: null,
                },
            );

            return;
        }

        if (linkedTaskQuery.isError) {
            toast.error("Unable to open task", {
                description: linkedTaskQuery.error instanceof Error
                    ? linkedTaskQuery.error.message
                    : "The task could not be found.",
            });

            void navigate(
                location.pathname,
                {
                    replace: true,
                    state: null,
                },
            );
        }
    }, [
        taskId,
        linkedTaskQuery.isSuccess,
        linkedTaskQuery.isError,
        linkedTaskQuery.data,
        linkedTaskQuery.error,
        navigate,
        location.pathname,
    ]);

    return (
        <main className={styles.root}>
            <PageHeader
                title="My Tasks"
                description="Keep track of your tasks and progress."
                actions={
                    <Button
                        variant="primary"
                        disabled={actionsPending}
                        onClick={handleCreateTask}
                    >
                        <Plus/>
                        New task
                    </Button>
                }
            />

            {statsQuery.isPending ? (
                <p className={styles.description}>
                    Loading task statistics...
                </p>
            ) : statsQuery.isError ? (
                <div className={styles.error}>
                    <p>
                        Unable to load task statistics.
                    </p>

                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                            void statsQuery.refetch();
                        }}
                    >
                        <RefreshCw/>
                        Retry
                    </Button>
                </div>
            ) : (
                <div className={styles.stats}>
                    <div className={styles.stat}>
                        <p className={styles.statLabel}>
                            To do
                        </p>

                        <p className={styles.statValue}>
                            {statsQuery.data.todo}
                        </p>
                    </div>

                    <div className={styles.stat}>
                        <p className={styles.statLabel}>
                            In progress
                        </p>

                        <p className={styles.statValue}>
                            {statsQuery.data.in_progress}
                        </p>
                    </div>

                    <div className={styles.stat}>
                        <p className={styles.statLabel}>
                            Completed
                        </p>

                        <p className={styles.statValue}>
                            {statsQuery.data.completed}
                        </p>
                    </div>
                </div>
            )}

            <section className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h2 className={styles.sectionTitle}>
                        {filter === "archived"
                            ? `Archived tasks (${tasksQuery.isSuccess ? totalItems : "—"})`
                            : `Tasks (${tasksQuery.isSuccess ? totalItems : "—"})`}
                    </h2>

                    <span className={styles.showingCount}>
                        {tasksQuery.isSuccess
                            ? `Showing ${tasks.length} of ${totalItems} tasks`
                            : "Task list"}
                    </span>
                </div>

                <div className={styles.toolbar}>
                    <div
                        className={styles.filters}
                        role="group"
                        aria-label="Filter tasks"
                    >
                        {filters.map((option) => (
                            <Button
                                key={option.value}
                                size="sm"
                                variant={
                                    filter === option.value
                                        ? "primary"
                                        : "secondary"
                                }
                                aria-pressed={filter === option.value}
                                onClick={() => {
                                    handleFilterChange(option.value);
                                }}
                            >
                                {option.label}
                            </Button>
                        ))}
                    </div>

                    <div className={styles.sortControl}>
                        <span className={styles.sortLabel}>
                            Sort by
                        </span>

                        <Select<TaskSortBy>
                            options={sortOptions}
                            value={sortBy}
                            onChange={(value) => {
                                if (value !== null) {
                                    handleSortChange(value);
                                }
                            }}
                            placeholder="Sort tasks"
                            className={styles.sortSelect}
                        />
                    </div>
                </div>

                {tasksQuery.isPending ? (
                    <p className={styles.description}>
                        Loading tasks...
                    </p>
                ) : tasksQuery.isError ? (
                    <div className={styles.error}>
                        <p>
                            Unable to load tasks. Please try again.
                        </p>

                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                                void tasksQuery.refetch();
                            }}
                        >
                            <RefreshCw/>
                            Retry
                        </Button>
                    </div>
                ) : tasks.length === 0 ? (
                    <div className={styles.empty}>
                        {filter === "archived"
                            ? "No archived tasks."
                            : filter === "all"
                                ? "You don't have any tasks yet. Tasks saved from NeuroLens conversations will appear here."
                                : "No tasks match the selected filter."}
                    </div>
                ) : (
                    <div className={styles.list}>
                        {tasks.map((task) => (
                            <TaskListItem
                                key={task.id}
                                task={task}
                                updating={actionsPending}
                                onStatusChange={handleStatusChange}
                                onEdit={handleEditTask}
                                onArchive={handleArchiveTask}
                                onRestore={handleRestoreTask}
                                onDelete={handleDeleteTask}
                                onSubtaskCompletionChange={(taskId, subtaskId, completed) => {
                                    subtaskMutation.mutate({
                                        taskId,
                                        subtaskId,
                                        completed,
                                    });
                                }}
                            />
                        ))}
                    </div>
                )}

                {tasksQuery.isSuccess && totalPages > 1 && (
                    <div className={styles.pagination}>
                        <Button
                            variant="secondary"
                            size="sm"
                            disabled={
                                page <= 1
                                || tasksQuery.isFetching
                            }
                            onClick={() => {
                                setPage((previous) => previous - 1);
                            }}
                        >
                            Previous
                        </Button>

                        <span className={styles.pageInfo}>
                            Page {page} of {totalPages}
                        </span>

                        <Button
                            variant="secondary"
                            size="sm"
                            disabled={
                                page >= totalPages
                                || tasksQuery.isFetching
                            }
                            onClick={() => {
                                setPage((previous) => previous + 1);
                            }}
                        >
                            Next
                        </Button>
                    </div>
                )}
            </section>

            {editorOpen && (
                <TaskEditorDialog
                    key={editingTask?.id ?? "new"}
                    task={editingTask}
                    saving={taskEditorMutation.isPending}
                    onClose={handleCloseEditor}
                    onSave={async (values) => {
                        await taskEditorMutation.mutateAsync({
                            task: editingTask,
                            values,
                        });
                    }}
                />
            )}

            <ConfirmationDialog
                open={deletingTask !== null}
                onClose={handleCloseDeleteDialog}
                onConfirm={handleConfirmDelete}
                loading={deleteMutation.isPending}
                destructive
                title="Delete task"
                description={
                    `Are you sure you want to delete "${deletingTask?.title ?? ""}"? ` +
                    "The task and its subtasks will be removed from My Tasks. " +
                    "The original conversation suggestion will remain marked as previously saved."
                }
                confirmLabel="Delete task"
            />
        </main>
    );
}
