import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, Pencil, Trash2 } from "lucide-react";
import { NavLink, useLocation, useNavigate } from "react-router";
import { toast } from "sonner";

import { cn } from "../../lib/cn";
import { type Conversation, deleteConversation, getConversations, renameConversation } from "../../lib/conversations";
import { Button } from "../button";
import { ConfirmationDialog } from "../dialog/ConfirmationDialog";
import { DropdownMenu } from "../dropdown-menu/DropdownMenu";
import { RenameConversationDialog } from "../../pages/chat/RenameConversationDialog";
import { recentConversationsStyles as styles } from "./RecentConversations.styles";

interface RecentConversationsProps {
    onNavigate?: () => void;
}

function formatConversationDate(value: string): string {
    const date = new Date(value);
    const today = new Date();

    if (date.toDateString() === today.toDateString()) {
        return "Today";
    }

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === yesterday.toDateString()) {
        return "Yesterday";
    }

    return new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
    }).format(date);
}

export function RecentConversations({
    onNavigate,
}: RecentConversationsProps) {
    const location = useLocation();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const [ expanded, setExpanded ] = useState(true);

    const [ renamingConversation, setRenamingConversation ] = useState<{
        id: string;
        title: string;
    } | null>(null);

    const [ deletingConversationId, setDeletingConversationId ] = useState<string | null>(null);

    const conversationsQuery = useQuery({
        queryKey: [ "conversations" ],
        queryFn: getConversations,
    });

    const selectedConversationId = new URLSearchParams(
        location.search,
    ).get("conversation");

    const conversations = conversationsQuery.data ?? [];

    const renameMutation = useMutation({
        mutationFn: ({
            conversationId,
            title,
        }: {
            conversationId: string;
            title: string;
        }) => renameConversation(conversationId, title),

        onSuccess: (conversation) => {
            setRenamingConversation(null);

            queryClient.setQueryData<Conversation[]>(
                [ "conversations" ],
                (previous = []) => previous.map((item) =>
                    item.id === conversation.id ? conversation : item,
                ),
            );

            void queryClient.invalidateQueries({
                queryKey: [ "conversations" ],
            });

            void queryClient.invalidateQueries({
                queryKey: [ "conversation", conversation.id ],
            });

            toast.success("Conversation renamed");
        },

        onError: (error) => {
            toast.error("Unable to rename conversation", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (conversationId: string) => deleteConversation(conversationId),

        onSuccess: (_result, conversationId) => {
            queryClient.setQueryData<Conversation[]>(
                [ "conversations" ],
                (previous = []) => previous.filter(
                    (conversation) => conversation.id !== conversationId,
                ),
            );

            queryClient.removeQueries({
                queryKey: [ "conversation", conversationId ],
            });

            if (
                location.pathname === "/app/chat"
                && selectedConversationId === conversationId
            ) {
                void navigate("/app/chat", { replace: true });
            }

            setDeletingConversationId(null);

            void queryClient.invalidateQueries({
                queryKey: [ "conversations" ],
            });

            toast.success("Conversation deleted");
        },

        onError: (error) => {
            toast.error("Unable to delete conversation", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const actionsDisabled = renameMutation.isPending || deleteMutation.isPending;

    return (
        <>
            <section
                className={styles.root}
                aria-label="Recent conversations"
            >
                <button
                    type="button"
                    className={styles.toggle}
                    aria-expanded={expanded}
                    aria-controls="sidebar-recent-conversations"
                    onClick={() => setExpanded((previous) => !previous)}
                >
                    <span className={styles.heading}>
                        Recent
                    </span>

                    <span className={styles.toggleRight}>
                        {conversationsQuery.isSuccess && (
                            <span className={styles.count}>
                                {conversations.length}
                            </span>
                        )}

                        <ChevronDown
                            className={cn(
                                styles.chevron,
                                !expanded && styles.chevronCollapsed,
                            )}
                        />
                    </span>
                </button>

                {expanded && (
                    <div
                        id="sidebar-recent-conversations"
                        className={styles.content}
                    >
                        {conversationsQuery.isPending && (
                            <p className={styles.empty}>
                                Loading conversations...
                            </p>
                        )}

                        {conversationsQuery.isError && (
                            <div className={styles.error} role="alert">
                                <p>Unable to load conversations.</p>

                                <Button
                                    variant="ghost"
                                    onClick={() => void conversationsQuery.refetch()}
                                >
                                    Try again
                                </Button>
                            </div>
                        )}

                        {conversationsQuery.isSuccess && conversations.length === 0 && (
                            <p className={styles.empty}>
                                No conversations yet.
                            </p>
                        )}

                        <nav
                            className={styles.list}
                            aria-label="Recent conversation links"
                        >
                            {conversations.map((conversation) => {
                                const active =
                                    location.pathname === "/app/chat"
                                    && selectedConversationId === conversation.id;

                                const title = conversation.title || "New conversation";

                                return (
                                    <div
                                        key={conversation.id}
                                        className={cn(
                                            styles.item,
                                            active && styles.active,
                                        )}
                                    >
                                        <NavLink
                                            to={`/app/chat?conversation=${conversation.id}`}
                                            className={styles.conversationLink}
                                            aria-current={active ? "page" : undefined}
                                            onClick={onNavigate}
                                        >
                                            <span
                                                className={cn(
                                                    styles.title,
                                                    active && styles.activeTitle,
                                                )}
                                                title={title}
                                            >
                                                {title}
                                            </span>

                                            <span className={styles.date}>
                                                {formatConversationDate(conversation.updated_at)}
                                            </span>
                                        </NavLink>

                                        <DropdownMenu
                                            label={`Actions for ${title}`}
                                            disabled={actionsDisabled}
                                            items={[
                                                {
                                                    label: "Rename",
                                                    icon: <Pencil className="size-4"/>,
                                                    onSelect: () => setRenamingConversation({
                                                        id: conversation.id,
                                                        title: conversation.title ?? "",
                                                    }),
                                                },
                                                {
                                                    label: "Delete",
                                                    icon: <Trash2 className="size-4"/>,
                                                    destructive: true,
                                                    onSelect: () => setDeletingConversationId(conversation.id),
                                                },
                                            ]}
                                        />
                                    </div>
                                );
                            })}
                        </nav>
                    </div>
                )}
            </section>

            <RenameConversationDialog
                open={renamingConversation !== null}
                title={renamingConversation?.title ?? ""}
                loading={renameMutation.isPending}
                onClose={() => {
                    if (!renameMutation.isPending) {
                        setRenamingConversation(null);
                    }
                }}
                onSave={(title) => {
                    if (!renamingConversation) {
                        return;
                    }

                    renameMutation.mutate({
                        conversationId: renamingConversation.id,
                        title,
                    });
                }}
            />

            <ConfirmationDialog
                open={deletingConversationId !== null}
                onClose={() => {
                    if (!deleteMutation.isPending) {
                        setDeletingConversationId(null);
                    }
                }}
                onConfirm={() => {
                    if (deletingConversationId && !deleteMutation.isPending) {
                        deleteMutation.mutate(deletingConversationId);
                    }
                }}
                loading={deleteMutation.isPending}
                destructive
                title="Delete conversation"
                description="This conversation and all its messages will be permanently deleted. This action cannot be undone."
                confirmLabel="Delete conversation"
            />
        </>
    );
}
