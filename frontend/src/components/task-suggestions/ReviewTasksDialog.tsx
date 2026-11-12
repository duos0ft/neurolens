import { type SyntheticEvent, useId, useRef, useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import type { ReviewedTask, TaskPriority } from "../../lib/tasks";

import { Button } from "../button";
import { DatePicker } from "../date-picker/DatePicker";
import { Dialog } from "../dialog";
import { Input } from "../input";
import { Select } from "../select/Select";
import { TimePicker } from "../time-picker/TimePicker";

import { reviewTasksDialogStyles as styles } from "./ReviewTasksDialog.styles";

interface ReviewTasksDialogProps {
    tasks: ReviewedTask[];
    saving: boolean;
    onClose: () => void;
    onSave: (tasks: ReviewedTask[]) => Promise<void>;
}

const PRIORITY_OPTIONS = [
    { label: "Low", value: "low" },
    { label: "Medium", value: "medium" },
    { label: "High", value: "high" },
] satisfies {
    label: string;
    value: Exclude<TaskPriority, null>;
}[];

/**
 * Convert an API time such as 23:59:00 into the
 * HH:mm format expected by the shared TimePicker.
 */
function toPickerTime(
    value: string | null | undefined,
): string | null {
    if (!value) {
        return null;
    }

    const match = /^(\d{2}):(\d{2})(?::00)?$/.exec(value);

    if (!match) {
        return null;
    }

    const hours = Number(match[1]);
    const minutes = Number(match[2]);

    if (hours > 23 || minutes > 59) {
        return null;
    }

    return `${match[1]}:${match[2]}`;
}

/**
 * Convert HH:mm into the API's HH:mm:ss format.
 */
function toApiTime(
    value: string | null | undefined,
): string | null {
    const normalized = toPickerTime(value);

    return normalized ? `${normalized}:00` : null;
}

export function ReviewTasksDialog({
    tasks,
    saving,
    onClose,
    onSave,
}: ReviewTasksDialogProps) {
    const formId = useId();
    const titleId = useId();
    const descriptionId = useId();
    const dueDateId = useId();
    const dueTimeId = useId();

    const formRef = useRef<HTMLFormElement>(null);

    const [ drafts, setDrafts ] = useState<ReviewedTask[]>(
        () => tasks.map((task) => ({
            ...task,
            due_time: toPickerTime(task.due_time),
            due_timezone: task.due_timezone ?? null,
            subtasks: task.subtasks.map((subtask) => ({
                ...subtask,
            })),
        })),
    );

    const [ activeIndex, setActiveIndex ] = useState(0);

    const [ validationError, setValidationError ] = useState<
        string | null
    >(null);

    const activeTask = drafts[activeIndex];

    function updateTask(changes: Partial<ReviewedTask>) {
        setDrafts((previous) =>
            previous.map((task, index) =>
                index === activeIndex
                    ? { ...task, ...changes }
                    : task,
            ),
        );

        setValidationError(null);
    }

    function updateSubtask(
        subtaskIndex: number,
        title: string,
    ) {
        if (!activeTask) {
            return;
        }

        updateTask({
            subtasks: activeTask.subtasks.map(
                (subtask, index) =>
                    index === subtaskIndex
                        ? { ...subtask, title }
                        : subtask,
            ),
        });
    }

    function addSubtask() {
        if (
            !activeTask
            || activeTask.subtasks.length >= 50
        ) {
            return;
        }

        updateTask({
            subtasks: [
                ...activeTask.subtasks,
                { title: "" },
            ],
        });
    }

    function removeSubtask(subtaskIndex: number) {
        if (!activeTask) {
            return;
        }

        updateTask({
            subtasks: activeTask.subtasks.filter(
                (_, index) => index !== subtaskIndex,
            ),
        });
    }

    function selectTask(index: number) {
        if (saving) {
            return;
        }

        setActiveIndex(index);
        setValidationError(null);
    }

    function updateDueDate(value: string | null) {
        if (!value) {
            updateTask({
                due_date: null,
                due_time: null,
                due_timezone: null,
            });

            return;
        }

        updateTask({
            due_date: value,
        });
    }

    function updateDueTime(value: string | null) {
        if (!value) {
            updateTask({
                due_time: null,
                due_timezone: null,
            });

            return;
        }

        updateTask({
            due_time: value,
        });
    }

    function handleSubmit(
        event: SyntheticEvent<HTMLFormElement>,
    ) {
        event.preventDefault();

        if (saving) {
            return;
        }

        // Ensure the editable TimePicker validates its current
        // draft before the form reads the committed value.
        const focusedElement = document.activeElement;

        if (
            focusedElement instanceof HTMLInputElement
            && formRef.current?.contains(focusedElement)
        ) {
            focusedElement.blur();
        }

        const invalidTimeInput =
            formRef.current?.querySelector(
                'input[aria-invalid="true"]',
            );

        if (invalidTimeInput) {
            setValidationError(
                "Please enter a valid deadline time (00:00–23:59).",
            );

            return;
        }

        const reviewedTasks = drafts.map((task) => {
            const dueDate = task.due_date || null;

            const dueTime = dueDate
                ? toApiTime(task.due_time)
                : null;

            return {
                ...task,

                title: task.title
                    .trim()
                    .replace(/\s+/g, " "),

                description:
                    task.description?.trim() || null,

                due_date: dueDate,

                due_time: dueTime,

                due_timezone: dueTime
                    ? task.due_timezone ?? null
                    : null,

                subtasks: task.subtasks.map((subtask) => ({
                    title: subtask.title
                        .trim()
                        .replace(/\s+/g, " "),
                })),
            };
        });

        const invalidIndex = reviewedTasks.findIndex(
            (task) =>
                !task.title
                || task.title.length > 200
                || (task.description?.length ?? 0) > 5000
                || task.subtasks.length > 50
                || task.subtasks.some(
                    (subtask) =>
                        !subtask.title
                        || subtask.title.length > 200,
                )
                || (
                    task.due_time !== null
                    && task.due_date === null
                ),
        );

        if (invalidIndex !== -1) {
            setActiveIndex(invalidIndex);

            setValidationError(
                `Please check the details for task ${
                    invalidIndex + 1
                }.`,
            );

            return;
        }

        setValidationError(null);

        void onSave(reviewedTasks).catch(() => {
            // The parent handles the notification.
            // Keep the dialog open for retrying.
        });
    }

    if (!activeTask) {
        return null;
    }

    const footer = (
        <div className={styles.footer}>
            <span className={styles.footerCount}>
                {drafts.length}{" "}
                {drafts.length === 1 ? "task" : "tasks"}{" "}
                to save
            </span>

            <div className={styles.footerActions}>
                <Button
                    type="button"
                    variant="secondary"
                    disabled={saving}
                    onClick={onClose}
                >
                    Cancel
                </Button>

                <Button
                    type="submit"
                    form={formId}
                    variant="primary"
                    disabled={saving}
                >
                    {saving
                        ? "Saving..."
                        : "Save to My Tasks"}
                </Button>
            </div>
        </div>
    );

    return (
        <Dialog
            open
            onClose={onClose}
            title="Review tasks"
            description="Make any changes before saving to My Tasks."
            size="xl"
            closeDisabled={saving}
            footer={footer}
        >
            <form
                ref={formRef}
                id={formId}
                className={styles.form}
                onSubmit={handleSubmit}
                noValidate
            >
                <nav
                    className={styles.taskNavigation}
                    aria-label="Tasks to review"
                >
                    {drafts.map((task, index) => (
                        <Button
                            key={task.suggestion_index}
                            type="button"
                            variant="ghost"
                            className={
                                index === activeIndex
                                    ? styles.taskTabActive
                                    : styles.taskTab
                            }
                            aria-current={
                                index === activeIndex
                                    ? "step"
                                    : undefined
                            }
                            onClick={() => selectTask(index)}
                            disabled={saving}
                        >
                            <span className={styles.taskNumber}>
                                {index + 1}
                            </span>

                            <span className={styles.taskTabTitle}>
                                {task.title.trim()
                                    || "Untitled task"}
                            </span>
                        </Button>
                    ))}
                </nav>

                <div className={styles.editor}>
                    <div className={styles.editorHeader}>
                        <span className={styles.taskIndicator}>
                            Task {activeIndex + 1} of{" "}
                            {drafts.length}
                        </span>
                    </div>

                    {validationError && (
                        <p
                            className={styles.validationError}
                            role="alert"
                        >
                            {validationError}
                        </p>
                    )}

                    {/* Task title */}

                    <div className={styles.field}>
                        <label
                            htmlFor={titleId}
                            className={styles.label}
                        >
                            Task title
                        </label>

                        <Input
                            id={titleId}
                            inputSize="md"
                            value={activeTask.title}
                            onChange={(event) =>
                                updateTask({
                                    title: event.target.value,
                                })
                            }
                            maxLength={200}
                            disabled={saving}
                            aria-required="true"
                        />
                    </div>

                    {/* Description */}

                    <div className={styles.field}>
                        <label
                            htmlFor={descriptionId}
                            className={styles.label}
                        >
                            Description
                        </label>

                        <textarea
                            id={descriptionId}
                            className={styles.textarea}
                            value={
                                activeTask.description ?? ""
                            }
                            onChange={(event) =>
                                updateTask({
                                    description:
                                    event.target.value,
                                })
                            }
                            maxLength={5000}
                            rows={3}
                            disabled={saving}
                            placeholder="Add helpful details..."
                        />
                    </div>

                    {/* Deadline */}

                    <div className={styles.deadlineSection}>
                        <div className={styles.deadlineHeader}>
                            <span className={styles.deadlineHeading}>
                                Deadline
                            </span>

                            <span className={styles.deadlineHint}>
                                Time is optional
                            </span>
                        </div>

                        <div className={styles.fieldGrid}>
                            <div className={styles.field}>
                                <label
                                    htmlFor={dueDateId}
                                    className={styles.label}
                                >
                                    Due date
                                </label>

                                <DatePicker
                                    id={dueDateId}
                                    value={activeTask.due_date}
                                    onChange={updateDueDate}
                                    disabled={saving}
                                />
                            </div>

                            <div className={styles.field}>
                                <label
                                    htmlFor={dueTimeId}
                                    className={styles.label}
                                >
                                    Due time
                                </label>

                                <TimePicker
                                    id={dueTimeId}
                                    key={
                                        activeTask.suggestion_index
                                    }
                                    value={
                                        activeTask.due_time ?? null
                                    }
                                    onChange={updateDueTime}
                                    disabled={
                                        saving
                                        || !activeTask.due_date
                                    }
                                    clearable
                                    interval={15}
                                />
                            </div>
                        </div>

                        <p className={styles.deadlineHint}>
                            {activeTask.due_date
                                ? activeTask.due_time
                                    ? "The deadline time is interpreted in the task's timezone."
                                    : "This task has a date-only deadline."
                                : "Choose a due date to enable the time picker."}
                        </p>
                    </div>

                    <div className={styles.field}>
                        <label className={styles.label}>
                            Priority
                        </label>

                        <Select<Exclude<TaskPriority, null>>
                            options={PRIORITY_OPTIONS}
                            value={activeTask.priority}
                            onChange={(priority) =>
                                updateTask({ priority })
                            }
                            placeholder="No priority"
                            disabled={saving}
                        />
                    </div>

                    {/* Subtasks */}

                    <div className={styles.subtaskSection}>
                        <div className={styles.subtaskHeader}>
                            <div>
                                <h3 className={styles.subtaskHeading}>
                                    Subtasks
                                </h3>

                                <p className={styles.subtaskHint}>
                                    Break this task into
                                    smaller actions.
                                </p>
                            </div>

                            <Button
                                type="button"
                                variant="ghost"
                                disabled={
                                    saving
                                    || activeTask.subtasks.length >= 50
                                }
                                onClick={addSubtask}
                            >
                                <Plus/>
                                Add
                            </Button>
                        </div>

                        {activeTask.subtasks.length === 0 && (
                            <p className={styles.emptySubtasks}>
                                No subtasks added.
                            </p>
                        )}

                        <div className={styles.subtaskList}>
                            {activeTask.subtasks.map(
                                (subtask, index) => (
                                    <div
                                        key={
                                            `${activeTask.suggestion_index}-${index}`
                                        }
                                        className={styles.subtaskRow}
                                    >
                                        <span
                                            className={
                                                styles.subtaskNumber
                                            }
                                        >
                                            {index + 1}.
                                        </span>

                                        <Input
                                            inputSize="md"
                                            value={subtask.title}
                                            onChange={(event) =>
                                                updateSubtask(
                                                    index,
                                                    event.target.value,
                                                )
                                            }
                                            placeholder="Subtask title"
                                            maxLength={200}
                                            disabled={saving}
                                            aria-label={
                                                `Subtask ${index + 1}`
                                            }
                                        />

                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            className={
                                                styles.removeSubtask
                                            }
                                            disabled={saving}
                                            onClick={() =>
                                                removeSubtask(index)
                                            }
                                            aria-label={
                                                `Remove subtask ${index + 1}`
                                            }
                                        >
                                            <Trash2/>
                                        </Button>
                                    </div>
                                ),
                            )}
                        </div>
                    </div>
                </div>
            </form>
        </Dialog>
    );
}
