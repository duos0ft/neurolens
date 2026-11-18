export const chatPageStyles = {
    root: [
        "flex h-full min-h-[30rem] min-w-0 flex-col",
        "overflow-hidden bg-bg",
    ].join(" "),

    workspace: [
        "flex min-h-0 min-w-0 flex-1",
        "overflow-hidden bg-bg",
    ].join(" "),

    chatArea: [
        "flex min-h-0 min-w-0 flex-1 flex-col",
        "bg-bg",
    ].join(" "),

    chatHeader: [
        "flex min-h-16 shrink-0 items-center",
        "justify-between gap-4",
        "border-b border-border",
        "bg-surface px-4 py-3 sm:px-6",
    ].join(" "),

    chatHeaderMain: [
        "flex min-w-0 flex-1 items-center gap-3",
    ].join(" "),

    chatHeaderContent: [
        "flex min-w-0 flex-col gap-0.5",
    ].join(" "),

    chatTitle: [
        "truncate text-sm font-semibold",
        "leading-ui text-fg",
    ].join(" "),

    chatSubtitle: [
        "truncate text-xs text-fg-muted",
    ].join(" "),

    headerActions: [
        "flex shrink-0 items-center gap-2",
    ].join(" "),

    newConversationButton: [
        "inline-flex items-center gap-2",
    ].join(" "),

    actionIcon: "size-4",

    emptyState: [
        "mx-auto flex w-full max-w-content",
        "min-h-0 flex-1 flex-col",
        "items-start justify-center gap-5",
        "px-5 py-10 sm:px-8",
    ].join(" "),

    emptyDescription: [
        "max-w-lg text-sm leading-relaxed",
        "text-fg-muted",
    ].join(" "),

    emptyActions: [
        "flex flex-wrap items-center gap-2",
    ].join(" "),

    emptyAction: [
        "rounded-lg border border-border",
        "bg-surface px-3 py-2",
        "text-sm font-medium text-fg-body",
        "transition-colors hover:bg-muted",
        "focus-visible:outline-2 focus-visible:outline-border-strong",
    ].join(" "),

    messages: [
        "flex min-h-0 flex-1 flex-col gap-10",
        "overflow-y-auto overscroll-contain",
        "bg-subtle px-4 py-7",
        "sm:px-8 sm:py-10",
    ].join(" "),

    messageRow: [
        "mx-auto flex w-full max-w-content",
        "items-start gap-3 sm:gap-4",
    ].join(" "),

    userMessageRow: [
        "mx-auto flex w-full max-w-content",
        "justify-end",
    ].join(" "),

    assistantAvatar: [
        "flex size-8 shrink-0 items-center justify-center",
        "rounded-lg bg-accent-soft",
        "text-accent",
    ].join(" "),

    assistantAvatarIcon: "size-4",

    userMessage: [
        "w-fit max-w-full",
        "rounded-bubble bg-primary",
        "px-4 py-3",
        "text-sm leading-relaxed text-on-primary",
    ].join(" "),

    assistantMessage: [
        "flex min-w-0 flex-1 flex-col",
        "text-sm leading-7 text-fg",
    ].join(" "),

    assistantMeta: [
        "mb-4 flex items-center gap-2",
        "text-eyebrow font-medium uppercase",
        "tracking-eyebrow text-fg-muted",
    ].join(" "),

    messageContent: [
        "whitespace-pre-wrap break-words",
        "leading-relaxed",
    ].join(" "),

    messageHint: [
        "mx-auto w-full max-w-content",
        "text-sm text-fg-muted",
    ].join(" "),

    messageError: [
        "mx-auto flex w-full max-w-content",
        "flex-col items-start gap-3",
        "text-sm text-neg-fg",
    ].join(" "),

    composerWrapper: [
        "shrink-0 bg-surface",
        "px-4 pb-5 pt-3 sm:px-8",
    ].join(" "),

    composer: [
        "mx-auto flex w-full max-w-content",
        "items-end gap-3 rounded-2xl",
        "border border-border bg-surface",
        "px-3 py-2 shadow-composer",
        "transition-[border-color,box-shadow] duration-150",
        "hover:border-border-strong",
        "focus-within:border-border-strong",
        "focus-within:shadow-popover",
    ].join(" "),

    messageInput: [
        "max-h-40 min-h-11 min-w-0 flex-1 resize-none",
        "overflow-y-auto border-0 bg-transparent",
        "px-2 py-2 text-sm leading-relaxed",
        "text-fg outline-none",
        "placeholder:text-fg-muted",
        "focus:outline-none focus:ring-0",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    sendButton: [
        "mb-1 flex !size-9 shrink-0 items-center",
        "justify-center !rounded-xl !p-0",
        "!shadow-none",
        "focus-visible:outline-2 focus-visible:outline-border-strong",
    ].join(" "),

    sendIcon: "size-4",

    composerHint: [
        "mx-auto mt-2 max-w-content",
        "text-center text-caption text-fg-muted",
    ].join(" "),

    userMessageGroup: [
        "flex w-fit max-w-[90%] flex-col items-end gap-2",
        "sm:max-w-[78%]",
    ].join(" "),

    assistantContent: [
        "min-w-0 max-w-3xl",
    ].join(" "),

    assistantExtras: [
        "mt-7 flex min-w-0 max-w-3xl",
        "flex-col gap-7",
    ].join(" "),

    assistantExtraSection: [
        "min-w-0",
    ].join(" "),

};
