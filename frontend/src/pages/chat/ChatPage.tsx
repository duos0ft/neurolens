import { type ChangeEvent, type KeyboardEvent, type SyntheticEvent, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowUp, MessageSquare, MessageSquarePlus, MessagesSquare, Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "../../components/button";
import { DropdownMenu } from "../../components/dropdown-menu/DropdownMenu";
import { PageHeader } from "../../components/page-header/PageHeader";
import {
    type Conversation,
    createConversation,
    deleteConversation,
    getConversation,
    getConversations,
    renameConversation,
    sendConversationMessage,
} from "../../lib/conversations";
import { chatPageStyles as styles } from "./ChatPage.styles";
import { RenameConversationDialog } from "./RenameConversationDialog";
import { ConfirmationDialog } from "../../components/dialog/ConfirmationDialog";

export function Component() {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesRef = useRef<HTMLDivElement>(null);

    const queryClient = useQueryClient();

    const [ selectedConversationId, setSelectedConversationId ] = useState<string | null>(null);
    const [ message, setMessage ] = useState("");

    const [ renamingConversation, setRenamingConversation ] = useState<{
        id: string;
        title: string;
    } | null>(null);

    const [ deletingConversationId, setDeletingConversationId ] = useState<string | null>(null);

    const conversationsQuery = useQuery({
        queryKey: [ "conversations" ],
        queryFn: getConversations,
    });

    const conversationQuery = useQuery({
        queryKey: [ "conversation", selectedConversationId ],
        queryFn: () => getConversation(selectedConversationId!),
        enabled: selectedConversationId !== null,
    });

    const createMutation = useMutation({
        mutationFn: () => createConversation(),

        onSuccess: (conversation) => {
            setSelectedConversationId(conversation.id);
            setMessage("");

            if (textareaRef.current) {
                textareaRef.current.style.height = "auto";
            }

            queryClient.setQueryData<Conversation[]>(
                [ "conversations" ],
                (previous = []) => [
                    conversation,
                    ...previous.filter((item) => item.id !== conversation.id),
                ],
            );

            void queryClient.invalidateQueries({
                queryKey: [ "conversations" ],
            });
        },

        onError: (error) => {
            toast.error("Unable to create conversation", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

    const sendMutation = useMutation({
        mutationFn: ({
            conversationId,
            content,
        }: {
            conversationId: string;
            content: string;
        }) => sendConversationMessage(conversationId, content),

        onSuccess: (_messages, variables) => {
            void queryClient.invalidateQueries({
                queryKey: [ "conversation", variables.conversationId ],
            });

            void queryClient.invalidateQueries({
                queryKey: [ "conversations" ],
            });
        },

        onError: (error) => {
            toast.error("Unable to send message", {
                description: error instanceof Error
                    ? error.message
                    : "Please try again.",
            });
        },
    });

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

            if (selectedConversationId === conversationId) {
                setSelectedConversationId(null);
                setMessage("");
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

    const conversations = conversationsQuery.data ?? [];

    function handleNewConversation() {
        if (createMutation.isPending || sendMutation.isPending) {
            return;
        }

        createMutation.mutate();
    }

    function handleSelectConversation(conversationId: string) {
        if (sendMutation.isPending) {
            return;
        }

        setSelectedConversationId(conversationId);
        setMessage("");

        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
    }

    function handleSendMessage(event: SyntheticEvent<HTMLFormElement>) {
        event.preventDefault();

        const content = message.trim();

        if (
            !selectedConversationId
            || !content
            || sendMutation.isPending
            || !conversationQuery.isSuccess
        ) {
            return;
        }

        sendMutation.mutate(
            {
                conversationId: selectedConversationId,
                content,
            },
            {
                onSuccess: () => {
                    setMessage("");

                    if (textareaRef.current) {
                        textareaRef.current.style.height = "auto";
                    }

                    textareaRef.current?.focus();
                },
            },
        );
    }

    function handleMessageChange(event: ChangeEvent<HTMLTextAreaElement>) {
        setMessage(event.target.value);

        const textarea = event.target;

        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    }

    function handleMessageKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
        if (
            event.key !== "Enter"
            || event.shiftKey
            || event.nativeEvent.isComposing
        ) {
            return;
        }

        event.preventDefault();

        if (
            !message.trim()
            || sendMutation.isPending
            || !conversationQuery.isSuccess
        ) {
            return;
        }

        event.currentTarget.form?.requestSubmit();
    }

    useEffect(() => {
        if (selectedConversationId && conversationQuery.isSuccess) {
            textareaRef.current?.focus();
        }
    }, [ selectedConversationId, conversationQuery.isSuccess ]);

    useEffect(() => {
        const container = messagesRef.current;

        if (!container) {
            return;
        }

        container.scrollTo({
            top: container.scrollHeight,
            behavior: "smooth",
        });
    }, [ conversationQuery.data?.messages.length, selectedConversationId ]);

    return (
        <div className={styles.root}>
            <PageHeader
                title="NeuroLens Assistant"
                description="Get help understanding workplace communication and organizing your tasks."
                actions={
                    <Button
                        variant="primary"
                        disabled={createMutation.isPending || sendMutation.isPending}
                        onClick={handleNewConversation}
                    >
                        <MessageSquarePlus className={styles.actionIcon}/>
                        {createMutation.isPending ? "Creating..." : "New conversation"}
                    </Button>
                }
            />

            <div className={styles.workspace}>
                <aside className={styles.conversationSidebar}>
                    <div className={styles.sidebarHeader}>
                        <h2 className={styles.sidebarTitle}>
                            Conversations
                        </h2>

                        {conversationsQuery.isSuccess && (
                            <span className={styles.sidebarCount}>
                                {conversations.length}
                            </span>
                        )}
                    </div>

                    {conversationsQuery.isPending && (
                        <p className={styles.sidebarHint}>
                            Loading conversations...
                        </p>
                    )}

                    {conversationsQuery.isError && (
                        <div className={styles.sidebarError} role="alert">
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
                        <p className={styles.sidebarHint}>
                            Your conversations will appear here.
                        </p>
                    )}

                    <div className={styles.conversationList}>
                        {conversations.map((conversation) => (
                            <div
                                key={conversation.id}
                                className={
                                    selectedConversationId === conversation.id
                                        ? styles.conversationActive
                                        : styles.conversationItem
                                }
                            >
                                <button
                                    type="button"
                                    disabled={sendMutation.isPending}
                                    className={styles.conversationSelect}
                                    onClick={() => handleSelectConversation(conversation.id)}
                                >
                                    <MessageSquare className={styles.conversationIcon}/>

                                    <span className={styles.conversationTitle}>
                                        {conversation.title || "New conversation"}
                                    </span>
                                </button>

                                <DropdownMenu
                                    label={`Actions for ${conversation.title || "New conversation"}`}
                                    disabled={
                                        sendMutation.isPending
                                        || renameMutation.isPending
                                        || deleteMutation.isPending
                                    }
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
                        ))}
                    </div>
                </aside>

                <section className={styles.chatArea} aria-label="Conversation">
                    {!selectedConversationId ? (
                        <div className={styles.emptyState}>
                            <div className={styles.emptyIcon}>
                                <MessageSquarePlus className={styles.emptyIconGraphic}/>
                            </div>

                            <h2 className={styles.emptyTitle}>
                                How can I help you today?
                            </h2>

                            <p className={styles.emptyDescription}>
                                I'm here to help you understand workplace communication,
                                organize your thoughts, and make complex tasks easier
                                to manage.
                            </p>
                        </div>
                    ) : (
                        <>
                            <div
                                ref={messagesRef}
                                className={styles.messages}
                                aria-live="polite"
                            >
                                {conversationQuery.isPending && (
                                    <p className={styles.messageHint}>
                                        Loading messages...
                                    </p>
                                )}

                                {conversationQuery.isError && (
                                    <div className={styles.messageError} role="alert">
                                        <p>Unable to load this conversation.</p>

                                        <Button
                                            variant="secondary"
                                            onClick={() => void conversationQuery.refetch()}
                                        >
                                            Try again
                                        </Button>
                                    </div>
                                )}

                                {conversationQuery.isSuccess
                                    && conversationQuery.data.messages.length === 0
                                    && !sendMutation.isPending && (
                                    <div className={styles.emptyState}>
                                        <div className={styles.emptyIcon}>
                                            <MessageSquarePlus className={styles.emptyIconGraphic}/>
                                        </div>

                                        <h2 className={styles.emptyTitle}>
                                            What's on your mind?
                                        </h2>

                                        <p className={styles.emptyDescription}>
                                            Ask me to clarify instructions, summarize
                                            information, or break a task into smaller steps.
                                        </p>
                                    </div>
                                )}

                                {conversationQuery.data?.messages.map((item) => (
                                    item.role === "user" ? (
                                        <div
                                            key={item.id}
                                            className={styles.userMessageRow}
                                        >
                                            <div className={styles.userMessage}>
                                                <p className={styles.messageContent}>
                                                    {item.content}
                                                </p>
                                            </div>
                                        </div>
                                    ) : (
                                        <div
                                            key={item.id}
                                            className={styles.messageRow}
                                        >
                                            <div className={styles.assistantAvatar}>
                                                <MessagesSquare className={styles.assistantAvatarIcon}/>
                                            </div>

                                            <div className={styles.assistantMessage}>
                                                <p className={styles.messageContent}>
                                                    {item.content}
                                                </p>
                                            </div>
                                        </div>
                                    )
                                ))}

                                {sendMutation.isPending && (
                                    <div className={styles.messageRow} role="status">
                                        <div className={styles.assistantAvatar}>
                                            <MessagesSquare className={styles.assistantAvatarIcon}/>
                                        </div>

                                        <p className={styles.messageHint}>
                                            NeuroLens is thinking...
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div className={styles.composerWrapper}>
                                <form
                                    className={styles.composer}
                                    onSubmit={handleSendMessage}
                                >
                                    <textarea
                                        ref={textareaRef}
                                        value={message}
                                        onKeyDown={handleMessageKeyDown}
                                        onChange={handleMessageChange}
                                        placeholder="Message NeuroLens..."
                                        className={styles.messageInput}
                                        maxLength={10000}
                                        disabled={
                                            sendMutation.isPending
                                            || !conversationQuery.isSuccess
                                        }
                                        aria-label="Message NeuroLens"
                                        rows={1}
                                    />

                                    <Button
                                        variant="primary"
                                        type="submit"
                                        className={styles.sendButton}
                                        disabled={
                                            !message.trim()
                                            || sendMutation.isPending
                                            || !conversationQuery.isSuccess
                                        }
                                        aria-label="Send message"
                                    >
                                        <ArrowUp className={styles.sendIcon}/>
                                    </Button>
                                </form>

                                <p className={styles.composerHint}>
                                    NeuroLens can make mistakes. Verify important information.
                                </p>
                            </div>
                        </>
                    )}
                </section>
            </div>

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
        </div>
    );
}
