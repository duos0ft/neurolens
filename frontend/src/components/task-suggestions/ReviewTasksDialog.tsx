import { type FormEvent, useId, useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import type { ReviewedTask, TaskPriority } from "../../lib/tasks";
import { Button } from "../button";
import { DatePicker } from "../date-picker/DatePicker";
import { Dialog } from "../dialog";
import { Input } from "../input";
import { reviewTasksDialogStyles as styles } from "./ReviewTasksDialog.styles";

interface ReviewTasksDialogProps {
    tasks: ReviewedTask[];
    saving: boolean;
    onClose: () => void;
    onSave: (tasks: ReviewedTask[]) => Promise<void>;
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
    const priorityId = useId();

    const [ drafts, setDrafts ] = useState<ReviewedTask[]>(
        () => tasks.map((task) => ({
            ...task,
            subtasks: task.subtasks.map((subtask) => ({
                ...subtask,
            })),
        })),
    );

    const [ activeIndex, setActiveIndex ] = useState(0);
    const [ validationError, setValidationError ] = useState<string | null>(null);

    const activeTask = drafts[activeIndex];

    function updateTask(changes: Partial<ReviewedTask>) {
        setDrafts((previous) => previous.map((task, index) =>
            index === activeIndex
                ? { ...task, ...changes }
                : task,
        ));

        setValidationError(null);
    }

    function updateSubtask(subtaskIndex: number, title: string) {
        if (!activeTask) {
            return;
        }

        updateTask({
            subtasks: activeTask.subtasks.map((subtask, index) =>
                index === subtaskIndex
                    ? { ...subtask, title }
                    : subtask,
            ),
        });
    }

    function addSubtask() {
        if (!activeTask || activeTask.subtasks.length >= 50) {
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
        setActiveIndex(index);
        setValidationError(null);
    }

    function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        if (saving) {
            return;
        }

        const reviewedTasks = drafts.map((task) => ({
            ...task,
            title: task.title.trim().replace(/\s+/g, " "),
            description: task.description?.trim() || null,
            subtasks: task.subtasks.map((subtask) => ({
                title: subtask.title.trim().replace(/\s+/g, " "),
            })),
        }));

        const invalidIndex = reviewedTasks.findIndex((task) =>
            !task.title
                || task.title.length > 200
                || (task.description?.length ?? 0) > 5000
                || task.subtasks.length > 50
                || task.subtasks.some((subtask) =>
                    !subtask.title || subtask.title.length > 200,
                ),
        );

        if (invalidIndex !== -1) {
            setActiveIndex(invalidIndex);
            setValidationError(
                `Please check the title, description, and subtasks for task ${invalidIndex + 1}.`,
            );
            return;
        }

        setValidationError(null);

        void onSave(reviewedTasks).catch(() => {
            // The parent handles the notification.
            // Keep the dialog open so the user can retry.
        });
    }

    if (!activeTask) {
        return null;
    }

    const footer = (
        <div className={styles.footer}>
            <span className={styles.footerCount}>
                {drafts.length} {drafts.length === 1 ? "task" : "tasks"} to save
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
                    {saving ? "Saving..." : "Save to My Tasks"}
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
            size="lg"
            closeDisabled={saving}
            footer={footer}
        >
            <form
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
                                {task.title.trim() || "Untitled task"}
                            </span>
                        </Button>
                    ))}
                </nav>

                <div className={styles.editor}>
                    <div className={styles.editorHeader}>
                        <span className={styles.taskIndicator}>
                            Task {activeIndex + 1} of {drafts.length}
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
                            onChange={(event) => updateTask({
                                title: event.target.value,
                            })}
                            maxLength={200}
                            disabled={saving}
                            aria-required="true"
                            aria-invalid={
                                !!validationError
                                && !activeTask.title.trim()
                            }
                        />
                    </div>

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
                            value={activeTask.description ?? ""}
                            onChange={(event) => updateTask({
                                description: event.target.value,
                            })}
                            maxLength={5000}
                            rows={3}
                            disabled={saving}
                            placeholder="Add helpful details..."
                        />
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
                                onChange={(date) => updateTask({
                                    due_date: date,
                                })}
                                disabled={saving}
                            />
                        </div>

                        <div className={styles.field}>
                            <label
                                htmlFor={priorityId}
                                className={styles.label}
                            >
                                Priority
                            </label>

                            <select
                                id={priorityId}
                                className={styles.select}
                                value={activeTask.priority ?? ""}
                                onChange={(event) => updateTask({
                                    priority: (
                                        event.target.value || null
                                    ) as TaskPriority,
                                })}
                                disabled={saving}
                            >
                                <option value="">No priority</option>
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                    </div>

                    <div className={styles.subtaskSection}>
                        <div className={styles.subtaskHeader}>
                            <div>
                                <h3 className={styles.subtaskHeading}>
                                    Subtasks
                                </h3>

                                <p className={styles.subtaskHint}>
                                    Break this task into smaller actions.
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
                            {activeTask.subtasks.map((subtask, index) => (
                                <div
                                    key={`${activeTask.suggestion_index}-${index}`}
                                    className={styles.subtaskRow}
                                >
                                    <span className={styles.subtaskNumber}>
                                        {index + 1}.
                                    </span>

                                    <Input
                                        inputSize="md"
                                        value={subtask.title}
                                        onChange={(event) => updateSubtask(
                                            index,
                                            event.target.value,
                                        )}
                                        placeholder="Subtask title"
                                        maxLength={200}
                                        disabled={saving}
                                        aria-label={`Subtask ${index + 1}`}
                                    />

                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className={styles.removeSubtask}
                                        disabled={saving}
                                        onClick={() => removeSubtask(index)}
                                        aria-label={`Remove subtask ${index + 1}`}
                                    >
                                        <Trash2/>
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </form>
        </Dialog>
    );
}
