import { type ChangeEvent, type KeyboardEvent, type SyntheticEvent, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowUp, MessageSquarePlus, MessagesSquare } from "lucide-react";
import { useSearchParams } from "react-router";
import { toast } from "sonner";

import { Button } from "../../components/button";
import { TaskSuggestions } from "../../components/task-suggestions/TaskSuggestions";
import {
    type Conversation,
    createConversation,
    getConversation,
    sendConversationMessage,
} from "../../lib/conversations";
import { ChatMessageContent } from "./ChatMessageContent";
import { chatPageStyles as styles } from "./ChatPage.styles";
import { CalendarSuggestions } from "../../components/calendar-suggestions/CalendarSuggestions";
import { SuggestedClarifications } from "../../components/suggested-clarifications/SuggestedClarifications";

export function Component() {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesRef = useRef<HTMLDivElement>(null);

    const queryClient = useQueryClient();
    const [ searchParams, setSearchParams ] = useSearchParams();
    const [ message, setMessage ] = useState("");

    const selectedConversationId = searchParams.get("conversation");

    const conversationQuery = useQuery({
        queryKey: [ "conversation", selectedConversationId ],
        queryFn: () => getConversation(selectedConversationId!),
        enabled: selectedConversationId !== null,
    });

    const createMutation = useMutation({
        mutationFn: createConversation,

        onSuccess: (conversation) => {
            setSearchParams(
                { conversation: conversation.id },
                { replace: true },
            );

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

    const conversationTitle = conversationQuery.data?.title ?? "New conversation";

    const isBusy = createMutation.isPending || sendMutation.isPending;
    const conversationReady = selectedConversationId !== null && conversationQuery.isSuccess;

    function handleNewConversation() {
        if (isBusy) {
            return;
        }

        createMutation.mutate();
    }

    function handleSendMessage(event: SyntheticEvent<HTMLFormElement>) {
        event.preventDefault();

        const content = message.trim();

        if (
            !selectedConversationId
            || !content
            || sendMutation.isPending
            || !conversationReady
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
            || !conversationReady
        ) {
            return;
        }

        event.currentTarget.form?.requestSubmit();
    }

    useEffect(() => {
        setMessage("");

        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
    }, [ selectedConversationId ]);

    useEffect(() => {
        if (conversationReady) {
            textareaRef.current?.focus();
        }
    }, [ conversationReady, selectedConversationId ]);

    useEffect(() => {
        const container = messagesRef.current;

        if (!container) {
            return;
        }

        container.scrollTo({
            top: container.scrollHeight,
            behavior: "instant",
        });
    }, [ conversationQuery.data?.messages.length, selectedConversationId ]);

    return (
        <div className={styles.root}>
            <div className={styles.workspace}>
                <section className={styles.chatArea} aria-label="Conversation">
                    <header className={styles.chatHeader}>
                        <div className={styles.chatHeaderMain}>
                            <div className={styles.chatHeaderContent}>
                                <h1 className={styles.chatTitle}>
                                    {selectedConversationId ? conversationTitle : "Assistant"}
                                </h1>

                                <span className={styles.chatSubtitle}>
                                    {selectedConversationId
                                        ? "NeuroLens"
                                        : "Workplace communication and task guidance"}
                                </span>
                            </div>
                        </div>

                        <div className={styles.headerActions}>
                            <Button
                                variant="primary"
                                className={styles.newConversationButton}
                                disabled={isBusy}
                                onClick={handleNewConversation}
                            >
                                <MessageSquarePlus className={styles.actionIcon}/>
                                {createMutation.isPending ? "Creating..." : "New conversation"}
                            </Button>
                        </div>
                    </header>

                    {!selectedConversationId ? (
                        <div className={styles.emptyState}>
                            <p className={styles.emptyDescription}>
                                Start a conversation to clarify workplace communication
                                or organize tasks into manageable actions.
                            </p>

                            <div className={styles.emptyActions}>
                                <button
                                    type="button"
                                    className={styles.emptyAction}
                                    disabled={isBusy}
                                    onClick={handleNewConversation}
                                >
                                    Start a conversation
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <div
                                ref={messagesRef}
                                className={styles.messages}
                                aria-label="Conversation messages"
                                aria-live="polite"
                                aria-relevant="additions"
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
                                        <p className={styles.emptyDescription}>
                                            Paste a workplace message to understand it,
                                            or describe work you'd like help organizing.
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
                                                <div className={styles.assistantMeta}>
                                                    NeuroLens
                                                </div>

                                                <ChatMessageContent content={item.content}/>

                                                {item.clarifications
                                                    && item.clarifications.questions.length > 0 && (
                                                    <SuggestedClarifications
                                                        key={item.id}
                                                        clarifications={item.clarifications}
                                                    />
                                                )}

                                                {item.task_suggestions && (
                                                    <TaskSuggestions
                                                        messageId={item.id}
                                                        suggestions={item.task_suggestions}
                                                    />
                                                )}

                                                {item.calendar_suggestions && (
                                                    <CalendarSuggestions
                                                        messageId={item.id}
                                                        suggestions={item.calendar_suggestions}
                                                    />
                                                )}
                                            </div>
                                        </div>
                                    )
                                ))}

                                {sendMutation.isPending && (
                                    <div
                                        className={styles.messageRow}
                                        role="status"
                                    >
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
                                        placeholder="Paste a message or ask a question..."
                                        className={styles.messageInput}
                                        maxLength={10000}
                                        disabled={!conversationReady || sendMutation.isPending}
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
                                            || !conversationReady
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
        </div>
    );
}
