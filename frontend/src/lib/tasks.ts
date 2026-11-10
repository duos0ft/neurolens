import { apiFetch } from "./api";

export type TaskPriority = "low" | "medium" | "high" | null;

export interface ReviewedSubtask {
    title: string;
}

export interface ReviewedTask {
    suggestion_index: number;
    title: string;
    description: string | null;
    priority: TaskPriority;
    due_date: string | null;
    subtasks: ReviewedSubtask[];
}

export interface SavedSubtask {
    id: string;
    task_id: string;
    title: string;
    completed: boolean;
    sort_order: number;
    created_at: string;
    updated_at: string;
}

export interface SavedTask {
    id: string;
    employee_id: string;
    title: string;
    description: string | null;
    status: "todo" | "in_progress" | "completed";
    priority: TaskPriority;
    due_date: string | null;
    source_message_id: string | null;
    source_suggestion_index: number | null;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    subtasks: SavedSubtask[];
}

export function saveReviewedTasks(
    messageId: string,
    tasks: ReviewedTask[],
): Promise<SavedTask[]> {
    return apiFetch<SavedTask[]>(
        "/api/tasks/from-reviewed-suggestions",
        {
            method: "POST",
            body: {
                message_id: messageId,
                tasks,
            },
        },
    );
}
