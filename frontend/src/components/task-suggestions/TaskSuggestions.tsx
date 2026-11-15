import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, CheckCircle2, History, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { cn } from "../../lib/cn";
import type { TaskSuggestions as TaskSuggestionsData } from "../../lib/conversations";
import {
    getSavedSuggestions,
    type ReviewedTask,
    type SavedSuggestion,
    type SavedSuggestionsResponse,
    saveReviewedTasks,
} from "../../lib/tasks";
import { Button } from "../button";
import { ReviewTasksDialog } from "./ReviewTasksDialog";
import { taskSuggestionsStyles as styles } from "./TaskSuggestions.styles";

interface TaskSuggestionsProps {
    messageId: string;
    suggestions: TaskSuggestionsData;
}

function getSuggestionLabel(suggestion: SavedSuggestion): string {
    if (suggestion.deleted) {
        return "Previously saved · Removed from My Tasks";
    }

    if (suggestion.archived) {
        return "Archived";
    }

    return "Saved to My Tasks";
}

export function TaskSuggestions({
    messageId,
    suggestions,
}: TaskSuggestionsProps) {
    const queryClient = useQueryClient();

    const [ selected, setSelected ] = useState<number[]>([]);
    const [ reviewOpen, setReviewOpen ] = useState(false);

    const savedSuggestionsKey = [
        "tasks",
        "saved-suggestions",
        messageId,
    ] as const;

    const savedSuggestionsQuery = useQuery({
        queryKey: savedSuggestionsKey,
        queryFn: () => getSavedSuggestions(messageId),
        enabled: suggestions.tasks.length > 0,
    });

    const savedSuggestions = savedSuggestionsQuery.data?.saved ?? [];

    const savedByIndex = new Map(
        savedSuggestions.map((suggestion) => [
            suggestion.suggestion_index,
            suggestion,
        ]),
    );

    const savedIndices = new Set(savedByIndex.keys());

    const savedCount = savedIndices.size;
    const totalCount = suggestions.tasks.length;

    const activeSavedCount = savedSuggestions.filter(
        (suggestion) => !suggestion.archived && !suggestion.deleted,
    ).length;

    const selectableIndices = selected.filter(
        (index) => !savedIndices.has(index),
    );

    const selectedTasks: ReviewedTask[] = suggestions.tasks
        .map((task, index) => ({
            suggestion_index: index,
            title: task.title,
            description: task.description,
            priority: task.priority,
            due_date: task.due_date,
            due_time: task.due_time ?? null,
            due_timezone: null,
            subtasks: task.subtasks.map((subtask) => ({
                title: subtask.title,
            })),
        }))
        .filter((task) =>
            selectableIndices.includes(task.suggestion_index),
        );

    const saveMutation = useMutation({
        mutationFn: (tasks: ReviewedTask[]) =>
            saveReviewedTasks(messageId, tasks),

        onSuccess: (tasks) => {
            queryClient.setQueryData<SavedSuggestionsResponse>(
                savedSuggestionsKey,
                (previous) => {
                    const savedByIndex = new Map(
                        (previous?.saved ?? []).map((suggestion) => [
                            suggestion.suggestion_index,
                            suggestion,
                        ]),
                    );

                    for (const task of tasks) {
                        if (task.source_suggestion_index !== null) {
                            savedByIndex.set(
                                task.source_suggestion_index,
                                {
                                    suggestion_index: task.source_suggestion_index,
                                    task_id: task.id,
                                    archived: task.archived_at !== null,
                                    deleted: task.deleted_at !== null,
                                },
                            );
                        }
                    }

                    return {
                        saved: [ ...savedByIndex.values() ].sort(
                            (a, b) =>
                                a.suggestion_index - b.suggestion_index,
                        ),
                    };
                },
            );

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
        if (
            savedIndices.has(index)
            || saveMutation.isPending
            || !savedSuggestionsQuery.isSuccess
        ) {
            return;
        }

        setSelected((previous) =>
            previous.includes(index)
                ? previous.filter((value) => value !== index)
                : [ ...previous, index ],
        );
    }

    if (suggestions.tasks.length === 0) {
        return null;
    }

    const description = savedCount === totalCount
        ? activeSavedCount === totalCount
            ? "All suggested tasks have been saved to My Tasks."
            : "All suggested tasks have been handled. Archived or removed tasks cannot be saved again."
        : savedCount > 0
            ? `${savedCount} of ${totalCount} tasks previously saved. Select any remaining tasks you'd like to keep.`
            : "Select the tasks you'd like to keep. Nothing will be added automatically.";

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
                        {totalCount} found
                    </span>
                </div>

                <p className={styles.description}>
                    {savedSuggestionsQuery.isSuccess
                        ? description
                        : savedSuggestionsQuery.isPending
                            ? "Checking previously saved tasks..."
                            : "Unable to determine which tasks have already been saved."}
                </p>

                <div className={styles.list}>
                    {suggestions.tasks.map((task, index) => {
                        const savedSuggestion = savedByIndex.get(index);
                        const isSaved = savedSuggestion !== undefined;

                        const isDeleted = savedSuggestion?.deleted ?? false;
                        const isArchived =
                            !isDeleted && (savedSuggestion?.archived ?? false);

                        return (
                            <div
                                key={index}
                                className={cn(
                                    styles.item,
                                    isSaved && styles.itemSaved,
                                )}
                            >
                                {isSaved ? (
                                    isDeleted ? (
                                        <History
                                            className={styles.removedIcon}
                                            aria-label="Previously saved and removed"
                                        />
                                    ) : isArchived ? (
                                        <Archive
                                            className={styles.archivedIcon}
                                            aria-label="Archived"
                                        />
                                    ) : (
                                        <CheckCircle2
                                            className={styles.savedIcon}
                                            aria-label="Saved"
                                        />
                                    )
                                ) : (
                                    <input
                                        type="checkbox"
                                        checked={selectableIndices.includes(index)}
                                        onChange={() => toggleSelected(index)}
                                        className={styles.checkbox}
                                        disabled={
                                            saveMutation.isPending
                                            || !savedSuggestionsQuery.isSuccess
                                        }
                                        aria-label={`Select ${task.title}`}
                                    />
                                )}

                                <div className={styles.itemContent}>
                                    <div className={styles.itemHeading}>
                                        <span className={styles.itemTitle}>
                                            {task.title}
                                        </span>

                                        {savedSuggestion && (
                                            <span
                                                className={cn(
                                                    styles.savedLabel,
                                                    (isArchived || isDeleted)
                                                    && styles.inactiveLabel,
                                                )}
                                            >
                                                {getSuggestionLabel(savedSuggestion)}
                                            </span>
                                        )}
                                    </div>

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
                                                    {task.due_time && ` at ${task.due_time.slice(0, 5)}`}
                                                </span>
                                            )}
                                        </div>
                                    )}

                                    {task.subtasks.length > 0 && (
                                        <ul className={styles.subtasks}>
                                            {task.subtasks.map(
                                                (subtask, subtaskIndex) => (
                                                    <li key={subtaskIndex}>
                                                        {subtask.title}
                                                    </li>
                                                ),
                                            )}
                                        </ul>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className={styles.footer}>
                    <span className={styles.selectedCount}>
                        {savedSuggestionsQuery.isPending
                            ? "Checking saved tasks..."
                            : savedSuggestionsQuery.isError
                                ? "Unable to check saved tasks"
                                : `${savedCount} previously saved · ${selectableIndices.length} selected`}
                    </span>

                    {savedCount < totalCount && (
                        <Button
                            type="button"
                            variant="primary"
                            disabled={
                                selectableIndices.length === 0
                                || saveMutation.isPending
                                || !savedSuggestionsQuery.isSuccess
                            }
                            onClick={() => setReviewOpen(true)}
                        >
                            <CheckCircle2/>
                            Review & Save
                        </Button>
                    )}
                </div>

                {savedSuggestionsQuery.isError && (
                    <Button
                        type="button"
                        variant="ghost"
                        onClick={() => {
                            void savedSuggestionsQuery.refetch();
                        }}
                    >
                        <RefreshCw/>
                        Retry checking saved tasks
                    </Button>
                )}
            </section>

            {reviewOpen && (
                <ReviewTasksDialog
                    tasks={selectedTasks}
                    saving={saveMutation.isPending}
                    onClose={() => {
                        if (!saveMutation.isPending) {
                            setReviewOpen(false);
                        }
                    }}
                    onSave={async (tasks) => {
                        await saveMutation.mutateAsync(tasks);
                    }}
                />
            )}
        </>
    );
}
