import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { TaskSuggestions as TaskSuggestionsData } from "../../lib/conversations";
import { type ReviewedTask, saveReviewedTasks } from "../../lib/tasks";
import { Button } from "../button";
import { ReviewTasksDialog } from "./ReviewTasksDialog";
import { taskSuggestionsStyles as styles } from "./TaskSuggestions.styles";

interface TaskSuggestionsProps {
    messageId: string;
    suggestions: TaskSuggestionsData;
}

export function TaskSuggestions({
    messageId,
    suggestions,
}: TaskSuggestionsProps) {
    const queryClient = useQueryClient();

    const [ selected, setSelected ] = useState<number[]>([]);
    const [ reviewOpen, setReviewOpen ] = useState(false);

    const saveMutation = useMutation({
        mutationFn: (tasks: ReviewedTask[]) =>
            saveReviewedTasks(messageId, tasks),

        onSuccess: (tasks) => {
            setReviewOpen(false);
            setSelected([]);

            void queryClient.invalidateQueries({
                queryKey: [ "tasks" ],
            });

            toast.success(
                tasks.length === 1
                    ? "Task saved to My Tasks"
                    : `${tasks.length} tasks saved to My Tasks`,
            );
        },

        onError: (error) => {
            toast.error("Unable to save tasks", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    function toggleSelected(index: number) {
        setSelected((previous) =>
            previous.includes(index)
                ? previous.filter((value) => value !== index)
                : [ ...previous, index ],
        );
    }

    const selectedTasks: ReviewedTask[] = suggestions.tasks
        .map((task, index) => ({
            suggestion_index: index,
            title: task.title,
            description: task.description,
            priority: task.priority,
            due_date: task.due_date,
            subtasks: task.subtasks.map((subtask) => ({
                title: subtask.title,
            })),
        }))
        .filter((task) => selected.includes(task.suggestion_index));

    if (suggestions.tasks.length === 0) {
        return (
            <div className={styles.empty}>
                No actionable tasks were identified in this message.
            </div>
        );
    }

    return (
        <>
            <section
                className={styles.root}
                aria-label="Suggested tasks"
            >
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
                                disabled={saveMutation.isPending}
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

                    <Button
                        type="button"
                        variant="primary"
                        disabled={
                            selected.length === 0
                            || saveMutation.isPending
                        }
                        onClick={() => setReviewOpen(true)}
                    >
                        Review & Save
                    </Button>
                </div>
            </section>

            {reviewOpen && (
                <ReviewTasksDialog
                    tasks={selectedTasks}
                    saving={saveMutation.isPending}
                    onClose={() => setReviewOpen(false)}
                    onSave={async (tasks) => {
                        await saveMutation.mutateAsync(tasks);
                    }}
                />
            )}
        </>
    );
}
