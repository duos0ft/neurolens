import { apiFetch } from "./api";

export type TaskPriority = "low" | "medium" | "high" | null;

export type TaskStatus = "todo" | "in_progress" | "completed";

export type TaskSortBy =
    | "created_at"
    | "updated_at"
    | "due_date"
    | "priority";

export type TaskSortOrder = "asc" | "desc";

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
    status: TaskStatus;
    priority: TaskPriority;
    due_date: string | null;
    source_message_id: string | null;
    source_suggestion_index: number | null;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    archived_at: string | null;
    deleted_at: string | null;
    subtasks: SavedSubtask[];
}

export interface SavedSuggestion {
    suggestion_index: number;
    task_id: string;
    archived: boolean;
    deleted: boolean;
}

export interface SavedSuggestionsResponse {
    saved: SavedSuggestion[];
}

export interface PageResponse<T> {
    items: T[];
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
}

export interface TaskFilters {
    page?: number;
    page_size?: number;
    status?: TaskStatus;
    priority?: Exclude<TaskPriority, null>;
    sort_by?: TaskSortBy;
    sort_order?: TaskSortOrder;
    archived?: boolean;
}

export interface TaskStats {
    todo: number;
    in_progress: number;
    completed: number;
}

export interface TaskInput {
    title: string;
    description: string | null;
    priority: TaskPriority;
    due_date: string | null;
    subtasks?: {
        id?: string;
        title: string;
    }[];
}

export function getSavedSuggestions(
    messageId: string,
): Promise<SavedSuggestionsResponse> {
    const params = new URLSearchParams({
        message_id: messageId,
    });

    return apiFetch<SavedSuggestionsResponse>(
        `/api/tasks/saved-suggestions?${params.toString()}`,
    );
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

export function getTasks(
    filters: TaskFilters = {},
): Promise<PageResponse<SavedTask>> {
    const params = new URLSearchParams();

    if (filters.page !== undefined) {
        params.set("page", String(filters.page));
    }

    if (filters.page_size !== undefined) {
        params.set("page_size", String(filters.page_size));
    }

    if (filters.status !== undefined) {
        params.set("status", filters.status);
    }

    if (filters.priority !== undefined) {
        params.set("priority", filters.priority);
    }

    if (filters.archived !== undefined) {
        params.set("archived", String(filters.archived));
    }

    if (filters.sort_by !== undefined) {
        params.set("sort_by", filters.sort_by);
    }

    if (filters.sort_order !== undefined) {
        params.set("sort_order", filters.sort_order);
    }

    const query = params.toString();

    return apiFetch<PageResponse<SavedTask>>(
        `/api/tasks${query ? `?${query}` : ""}`,
    );
}

export function getTaskStats(): Promise<TaskStats> {
    return apiFetch<TaskStats>("/api/tasks/stats");
}

export function updateTaskStatus(
    taskId: string,
    status: TaskStatus,
): Promise<SavedTask> {
    return apiFetch<SavedTask>(
        `/api/tasks/${taskId}/status`,
        {
            method: "PATCH",
            body: { status },
        },
    );
}

export function createTask(
    task: TaskInput,
): Promise<SavedTask> {
    return apiFetch<SavedTask>(
        "/api/tasks",
        {
            method: "POST",
            body: task,
        },
    );
}

export function updateTask(
    taskId: string,
    task: TaskInput,
): Promise<SavedTask> {
    return apiFetch<SavedTask>(
        `/api/tasks/${taskId}`,
        {
            method: "PATCH",
            body: task,
        },
    );
}

export function archiveTask(
    taskId: string,
): Promise<SavedTask> {
    return apiFetch<SavedTask>(
        `/api/tasks/${taskId}/archive`,
        {
            method: "PATCH",
        },
    );
}

export function restoreTask(
    taskId: string,
): Promise<SavedTask> {
    return apiFetch<SavedTask>(
        `/api/tasks/${taskId}/restore`,
        {
            method: "PATCH",
        },
    );
}

export function deleteTask(
    taskId: string,
): Promise<void> {
    return apiFetch<void>(
        `/api/tasks/${taskId}`,
        {
            method: "DELETE",
        },
    );
}

export function updateSubtaskCompletion(
    taskId: string,
    subtaskId: string,
    completed: boolean,
): Promise<SavedSubtask> {
    return apiFetch<SavedSubtask>(
        `/api/tasks/${taskId}/subtasks/${subtaskId}/completion`,
        {
            method: "PATCH",
            body: {
                completed,
            },
        },
    );
}
