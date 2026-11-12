import { type SyntheticEvent, useId, useRef, useState } from "react";
import { ArrowDown, ArrowUp, Check, Plus, Trash2 } from "lucide-react";

import { Button } from "../../components/button";
import { DatePicker } from "../../components/date-picker/DatePicker";
import { Dialog } from "../../components/dialog";
import { Input } from "../../components/input";
import { Select } from "../../components/select/Select";
import { TimePicker } from "../../components/time-picker/TimePicker";
import type { SavedTask, TaskInput, TaskPriority } from "../../lib/tasks";
import { taskEditorDialogStyles as styles } from "./TaskEditorDialog.styles";

interface TaskEditorDialogProps {
    task?: SavedTask | null;
    saving: boolean;
    onClose: () => void;
    onSave: (values: TaskInput) => Promise<void>;
}

interface DraftSubtask {
    key: string;
    id?: string;
    title: string;
}

const MAX_SUBTASKS = 50;

const priorityOptions: {
    label: string;
    value: Exclude<TaskPriority, null>;
}[] = [
    { label: "Low", value: "low" },
    { label: "Medium", value: "medium" },
    { label: "High", value: "high" },
];

function toPickerTime(value: string | null | undefined): string | null {
    if (!value) {
        return null;
    }

    const match = /^([01]\d|2[0-3]):([0-5]\d)(?::00)?$/.exec(value);

    return match ? `${match[1]}:${match[2]}` : null;
}

function toApiTime(value: string | null): string | null {
    if (!value) {
        return null;
    }

    return /^([01]\d|2[0-3]):[0-5]\d$/.test(value)
        ? `${value}:00`
        : null;
}

export function TaskEditorDialog({
    task,
    saving,
    onClose,
    onSave,
}: TaskEditorDialogProps) {
    const formId = useId();
    const titleId = useId();
    const descriptionId = useId();
    const dueDateId = useId();
    const dueTimeId = useId();

    const formRef = useRef<HTMLFormElement>(null);
    const nextSubtaskKey = useRef(0);

    const [ title, setTitle ] = useState(task?.title ?? "");

    const [ description, setDescription ] = useState(
        task?.description ?? "",
    );

    const [ priority, setPriority ] = useState<TaskPriority>(
        task?.priority ?? null,
    );

    const [ dueDate, setDueDate ] = useState<string | null>(
        task?.due_date ?? null,
    );

    const [ dueTime, setDueTime ] = useState<string | null>(
        toPickerTime(task?.due_time),
    );

    const [ dueTimezone, setDueTimezone ] = useState<string | null>(
        task?.due_timezone ?? null,
    );

    const [ subtasks, setSubtasks ] = useState<DraftSubtask[]>(
        () => [ ...(task?.subtasks ?? []) ]
            .sort((a, b) => a.sort_order - b.sort_order)
            .map((subtask) => ({
                key: subtask.id,
                id: subtask.id,
                title: subtask.title,
            })),
    );

    const [ validationError, setValidationError ] = useState<string | null>(null);

    const editing = Boolean(task);

    function updateDueDate(value: string | null) {
        setDueDate(value);

        if (!value) {
            setDueTime(null);
            setDueTimezone(null);
        }

        setValidationError(null);
    }

    function updateDueTime(value: string | null) {
        setDueTime(value);

        if (!value) {
            setDueTimezone(null);
        }

        setValidationError(null);
    }

    function updateSubtask(key: string, title: string) {
        setSubtasks((previous) => previous.map((subtask) =>
            subtask.key === key
                ? { ...subtask, title }
                : subtask,
        ));

        setValidationError(null);
    }

    function addSubtask() {
        if (saving || subtasks.length >= MAX_SUBTASKS) {
            return;
        }

        const key = `new-${nextSubtaskKey.current++}`;

        setSubtasks((previous) => [
            ...previous,
            {
                key,
                title: "",
            },
        ]);

        setValidationError(null);
    }

    function removeSubtask(key: string) {
        if (saving) {
            return;
        }

        setSubtasks((previous) => previous.filter(
            (subtask) => subtask.key !== key,
        ));

        setValidationError(null);
    }

    function moveSubtask(index: number, direction: -1 | 1) {
        if (saving) {
            return;
        }

        setSubtasks((previous) => {
            const nextIndex = index + direction;

            if (nextIndex < 0 || nextIndex >= previous.length) {
                return previous;
            }

            const updated = [ ...previous ];

            [ updated[index], updated[nextIndex] ] = [
                updated[nextIndex],
                updated[index],
            ];

            return updated;
        });

        setValidationError(null);
    }

    function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
        event.preventDefault();

        if (saving) {
            return;
        }

        const normalizedTitle = title.trim().replace(/\s+/g, " ");
        const normalizedDescription = description.trim() || null;

        if (!normalizedTitle || normalizedTitle.length > 200) {
            setValidationError(
                "Task title must contain between 1 and 200 characters.",
            );
            return;
        }

        if (normalizedDescription && normalizedDescription.length > 5000) {
            setValidationError(
                "Description cannot exceed 5000 characters.",
            );
            return;
        }

        const timeInput = formRef.current?.querySelector<HTMLInputElement>(
            `input[id="${CSS.escape(dueTimeId)}"]`,
        );

        const enteredTime = dueDate
            ? timeInput?.value.trim() ?? dueTime ?? ""
            : "";

        if (
            dueDate
            && enteredTime
            && !/^([01]\d|2[0-3]):[0-5]\d$/.test(enteredTime)
        ) {
            setValidationError(
                "Enter a valid deadline time between 00:00 and 23:59.",
            );
            return;
        }

        const normalizedDueTime = dueDate
            ? toApiTime(enteredTime || null)
            : null;

        if (subtasks.length > MAX_SUBTASKS) {
            setValidationError(
                `A task cannot have more than ${MAX_SUBTASKS} subtasks.`,
            );
            return;
        }

        const normalizedSubtasks = subtasks.map((subtask) => ({
            ...(subtask.id ? { id: subtask.id } : {}),
            title: subtask.title.trim().replace(/\s+/g, " "),
        }));

        if (normalizedSubtasks.some(
            (subtask) => !subtask.title || subtask.title.length > 200,
        )) {
            setValidationError(
                "Every subtask must have a title between 1 and 200 characters.",
            );
            return;
        }

        setValidationError(null);

        void onSave({
            title: normalizedTitle,
            description: normalizedDescription,
            priority,
            due_date: dueDate,
            due_time: normalizedDueTime,
            due_timezone: normalizedDueTime ? dueTimezone : null,
            subtasks: normalizedSubtasks,
        }).catch(() => {
        });
    }

    const footer = (
        <div className={styles.footer}>
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
                {editing ? <Check/> : <Plus/>}

                {saving
                    ? "Saving..."
                    : editing
                        ? "Save changes"
                        : "Create task"}
            </Button>
        </div>
    );

    return (
        <Dialog
            open
            onClose={onClose}
            title={editing ? "Edit task" : "New task"}
            description={
                editing
                    ? "Update the details of your task."
                    : "Create a task to keep track of your work."
            }
            size="md"
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
                {validationError && (
                    <p className={styles.validationError} role="alert">
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
                        value={title}
                        onChange={(event) => {
                            setTitle(event.target.value);
                            setValidationError(null);
                        }}
                        maxLength={200}
                        disabled={saving}
                        aria-required="true"
                        placeholder="What needs to be done?"
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
                        value={description}
                        onChange={(event) => {
                            setDescription(event.target.value);
                            setValidationError(null);
                        }}
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
                            value={dueDate}
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
                            value={dueTime}
                            onChange={updateDueTime}
                            disabled={saving || !dueDate}
                            clearable
                            interval={15}
                        />
                    </div>
                </div>

                <div className={styles.field}>
                    <label className={styles.label}>
                        Priority
                    </label>

                    <Select<Exclude<TaskPriority, null>>
                        options={priorityOptions}
                        value={priority}
                        onChange={(value) => {
                            setPriority(value);
                            setValidationError(null);
                        }}
                        placeholder="No priority"
                        disabled={saving}
                    />
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
                            size="sm"
                            disabled={saving || subtasks.length >= MAX_SUBTASKS}
                            onClick={addSubtask}
                        >
                            <Plus/>
                            Add
                        </Button>
                    </div>

                    {subtasks.length === 0 ? (
                        <p className={styles.emptySubtasks}>
                            No subtasks added.
                        </p>
                    ) : (
                        <div className={styles.subtaskList}>
                            {subtasks.map((subtask, index) => (
                                <div
                                    key={subtask.key}
                                    className={styles.subtaskRow}
                                >
                                    <span className={styles.subtaskNumber}>
                                        {index + 1}.
                                    </span>

                                    <Input
                                        inputSize="md"
                                        value={subtask.title}
                                        onChange={(event) => {
                                            updateSubtask(
                                                subtask.key,
                                                event.target.value,
                                            );
                                        }}
                                        maxLength={200}
                                        disabled={saving}
                                        placeholder="Subtask title"
                                        aria-label={`Subtask ${index + 1}`}
                                        className={styles.subtaskInput}
                                    />

                                    <div className={styles.subtaskActions}>
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            disabled={saving || index === 0}
                                            onClick={() => moveSubtask(index, -1)}
                                            aria-label={`Move subtask ${index + 1} up`}
                                            className={styles.subtaskAction}
                                        >
                                            <ArrowUp/>
                                        </Button>

                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            disabled={
                                                saving
                                                || index === subtasks.length - 1
                                            }
                                            onClick={() => moveSubtask(index, 1)}
                                            aria-label={`Move subtask ${index + 1} down`}
                                            className={styles.subtaskAction}
                                        >
                                            <ArrowDown/>
                                        </Button>

                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            disabled={saving}
                                            onClick={() => removeSubtask(subtask.key)}
                                            aria-label={`Remove subtask ${index + 1}`}
                                            className={styles.removeSubtask}
                                        >
                                            <Trash2/>
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </form>
        </Dialog>
    );
}
