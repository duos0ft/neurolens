import { Archive, CheckCircle2, Circle, Clock3, ListRestart, Pencil, Play, RotateCcw, Trash2 } from "lucide-react";

import { taskListItemStyles as styles } from "./TaskListItem.styles";
import { DropdownMenu } from "../../components/dropdown-menu/DropdownMenu";
import { ListItem } from "../../components/list-item";
import type { SavedTask, TaskStatus } from "../../lib/tasks";

interface TaskListItemProps {
    task: SavedTask;
    updating?: boolean;
    onStatusChange: (taskId: string, status: TaskStatus) => void;
    onEdit: (task: SavedTask) => void;
    onArchive: (taskId: string) => void;
    onRestore: (taskId: string) => void;
    onDelete: (task: SavedTask) => void;
    onSubtaskCompletionChange: (
        taskId: string,
        subtaskId: string,
        completed: boolean,
    ) => void;
}

const statusLabels: Record<TaskStatus, string> = {
    todo: "To do",
    in_progress: "In progress",
    completed: "Completed",
};

function formatDueDate(value: string): string {
    const date = new Date(`${value.slice(0, 10)}T00:00:00Z`);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return new Intl.DateTimeFormat("en", {
        month: "short",
        day: "numeric",
        timeZone: "UTC",
    }).format(date);
}

function formatDueTime(value: string): string {
    const match = /^([01]\d|2[0-3]):([0-5]\d)(?::\d{2})?$/.exec(value);

    if (!match) {
        return value;
    }

    return `${match[1]}:${match[2]}`;
}

export function TaskListItem({
    task,
    updating = false,
    onStatusChange,
    onEdit,
    onRestore,
    onArchive,
    onDelete,
    onSubtaskCompletionChange,
}: TaskListItemProps) {
    const isCompleted = task.status === "completed";

    const completedSubtasks = task.subtasks.filter(
        (subtask) => subtask.completed,
    ).length;

    const statusActions = task.status === "todo"
        ? [
            {
                label: "Start progress",
                icon: <Play/>,
                onSelect: () => onStatusChange(task.id, "in_progress"),
            },
            {
                label: "Mark completed",
                icon: <CheckCircle2/>,
                onSelect: () => onStatusChange(task.id, "completed"),
            },
        ]
        : task.status === "in_progress"
            ? [
                {
                    label: "Move to To do",
                    icon: <ListRestart/>,
                    onSelect: () => onStatusChange(task.id, "todo"),
                },
                {
                    label: "Mark completed",
                    icon: <CheckCircle2/>,
                    onSelect: () => onStatusChange(task.id, "completed"),
                },
            ]
            : [
                {
                    label: "Reopen",
                    icon: <RotateCcw/>,
                    onSelect: () => onStatusChange(task.id, "todo"),
                },
            ];

    return (
        <ListItem
            title={task.title}
            description={task.description}
            selected={isCompleted}
            leading={
                <button
                    type="button"
                    className={styles.statusButton}
                    disabled={updating || task.archived_at !== null}
                    aria-label={
                        isCompleted
                            ? `Reopen ${task.title}`
                            : `Complete ${task.title}`
                    }
                    title={
                        isCompleted
                            ? "Reopen task"
                            : "Mark completed"
                    }
                    onClick={() => {
                        onStatusChange(
                            task.id,
                            isCompleted ? "todo" : "completed",
                        );
                    }}
                >
                    {isCompleted ? (
                        <CheckCircle2
                            className={styles.completedIcon}
                            aria-hidden="true"
                        />
                    ) : task.status === "in_progress" ? (
                        <Clock3
                            className={styles.statusIcon}
                            aria-hidden="true"
                        />
                    ) : (
                        <Circle
                            className={styles.statusIcon}
                            aria-hidden="true"
                        />
                    )}
                </button>
            }
            actions={

                <DropdownMenu
                    label={`Actions for ${task.title}`}
                    disabled={updating}
                    items={
                        task.archived_at
                            ? [
                                {
                                    label: "Restore task",
                                    icon: <RotateCcw/>,
                                    onSelect: () => onRestore(task.id),
                                },
                                {
                                    label: "Delete task",
                                    icon: <Trash2/>,
                                    destructive: true,
                                    separatorBefore: true,
                                    onSelect: () => onDelete(task),
                                },
                            ]
                            : [
                                {
                                    label: "Edit task",
                                    icon: <Pencil/>,
                                    onSelect: () => onEdit(task),
                                },
                                ...statusActions,
                                {
                                    label: "Archive task",
                                    icon: <Archive/>,
                                    separatorBefore: true,
                                    onSelect: () => onArchive(task.id),
                                },
                                {
                                    label: "Delete task",
                                    icon: <Trash2/>,
                                    destructive: true,
                                    onSelect: () => onDelete(task),
                                },
                            ]
                    }
                />
            }
            metadata={
                <>
                    <span>{statusLabels[task.status]}</span>

                    {task.priority && (
                        <>
                            <span aria-hidden="true">·</span>
                            <span>
                                {task.priority.charAt(0).toUpperCase()
                                    + task.priority.slice(1)} priority
                            </span>
                        </>
                    )}

                    {task.due_date && (
                        <>
                            <span aria-hidden="true">·</span>
                            <span>
                                Due {formatDueDate(task.due_date)}
                                {task.due_time && (
                                    <>
                                        {" at "}
                                        {formatDueTime(task.due_time)}
                                    </>
                                )}
                                {task.due_time && task.due_timezone && (
                                    <span className="ml-1 text-fg-muted">
                                        ({task.due_timezone})
                                    </span>
                                )}
                            </span>
                        </>
                    )}

                    {task.source_message_id && (
                        <>
                            <span aria-hidden="true">·</span>
                            <span>Suggested by NeuroLens</span>
                        </>
                    )}
                </>
            }
        >

            {task.subtasks.length > 0 && (
                <div className={styles.subtaskContent}>
                    <div className={styles.subtaskHeader}>
                        <span className={styles.subtaskCount}>
                            Subtasks
                        </span>

                        <span className={styles.subtaskCount}>
                            {completedSubtasks} of {task.subtasks.length} completed
                        </span>
                    </div>

                    <div
                        className={styles.progressTrack}
                        role="progressbar"
                        aria-label={`Subtask progress for ${task.title}`}
                        aria-valuemin={0}
                        aria-valuemax={task.subtasks.length}
                        aria-valuenow={completedSubtasks}
                    >
                        <div
                            className={styles.progressFill}
                            style={{
                                width: `${completedSubtasks / task.subtasks.length * 100}%`,
                            }}
                        />
                    </div>

                    <ul className={styles.subtasks}>
                        {[ ...task.subtasks ]
                            .sort((a, b) => a.sort_order - b.sort_order)
                            .map((subtask) => (
                                <li
                                    key={subtask.id}
                                    className={styles.subtaskRow}
                                >
                                    <input
                                        type="checkbox"
                                        checked={subtask.completed}
                                        disabled={updating || task.archived_at !== null}
                                        onChange={(event) => {
                                            onSubtaskCompletionChange(
                                                task.id,
                                                subtask.id,
                                                event.target.checked,
                                            );
                                        }}
                                        aria-label={`${subtask.completed ? "Reopen" : "Complete"} ${subtask.title}`}
                                        className={styles.subtaskCheckbox}
                                    />

                                    <span
                                        className={
                                            subtask.completed
                                                ? styles.subtaskCompleted
                                                : styles.subtaskTitle
                                        }
                                    >
                                        {subtask.title}
                                    </span>
                                </li>
                            ))}
                    </ul>
                </div>
            )}
        </ListItem>
    );
}
