import { useState } from "react";

import type { ExtractedTask, TaskSuggestions as TaskSuggestionsData } from "../../lib/conversations";
import { taskSuggestionsStyles as styles } from "./TaskSuggestions.styles";

interface TaskSuggestionsProps {
    suggestions: TaskSuggestionsData;
    onConfirm?: (tasks: ExtractedTask[]) => void;
}

export function TaskSuggestions({
    suggestions,
    onConfirm,
}: TaskSuggestionsProps) {
    const [ selected, setSelected ] = useState<number[]>([]);

    function toggleSelected(index: number) {
        setSelected((previous) =>
            previous.includes(index)
                ? previous.filter((value) => value !== index)
                : [ ...previous, index ],
        );
    }

    const selectedTasks = suggestions.tasks.filter(
        (_, index) => selected.includes(index),
    );

    if (suggestions.tasks.length === 0) {
        return (
            <div className={styles.empty}>
                No actionable tasks were identified in this message.
            </div>
        );
    }

    return (
        <section className={styles.root} aria-label="Suggested tasks">
            <div className={styles.header}>
                <h3 className={styles.title}>
                    Suggested tasks
                </h3>

                <span className={styles.count}>
                    {suggestions.tasks.length} found
                </span>
            </div>

            <p className={styles.description}>
                Select the tasks you'd like to keep.
                Nothing will be added automatically.
            </p>

            <div className={styles.list}>
                {suggestions.tasks.map((task, index) => (
                    <label
                        key={index}
                        className={styles.item}
                    >
                        <input
                            type="checkbox"
                            checked={selected.includes(index)}
                            onChange={() => toggleSelected(index)}
                            className={styles.checkbox}
                        />

                        <div className={styles.itemContent}>
                            <span className={styles.itemTitle}>
                                {task.title}
                            </span>

                            {task.description && (
                                <p className={styles.itemDescription}>
                                    {task.description}
                                </p>
                            )}

                            {(task.priority || task.due_date) && (
                                <div className={styles.metadata}>
                                    {task.priority && (
                                        <span>
                                            Priority: {task.priority}
                                        </span>
                                    )}

                                    {task.due_date && (
                                        <span>
                                            Due: {task.due_date}
                                        </span>
                                    )}
                                </div>
                            )}

                            {task.subtasks.length > 0 && (
                                <ul className={styles.subtasks}>
                                    {task.subtasks.map((subtask, subtaskIndex) => (
                                        <li key={subtaskIndex}>
                                            {subtask.title}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    </label>
                ))}
            </div>

            <div className={styles.footer}>
                <span className={styles.selectedCount}>
                    {selected.length} selected
                </span>

                {onConfirm && (
                    <button
                        type="button"
                        disabled={selectedTasks.length === 0}
                        onClick={() => onConfirm(selectedTasks)}
                    >
                        Add {selectedTasks.length} to My Tasks
                    </button>
                )}
            </div>
        </section>
    );
}
