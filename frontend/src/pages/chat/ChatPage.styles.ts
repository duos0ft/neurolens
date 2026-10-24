export const chatPageStyles = {
    root: [
        "flex h-[calc(100dvh-7rem)] min-h-[32rem]",
        "w-full flex-col gap-6",
    ].join(" "),
    actionIcon: "size-4",

    workspace: [
        "flex min-h-0 flex-1 flex-col overflow-hidden",
        "rounded-xl border border-border bg-surface",
        "md:flex-row",
    ].join(" "),

    conversationSidebar: [
        "flex max-h-48 shrink-0 flex-col gap-3",
        "border-b border-border bg-surface p-4",
        "md:max-h-none md:w-64 md:border-b-0 md:border-r",
    ].join(" "),
    conversationSelect: [
        "flex min-w-0 flex-1 items-center gap-3",
        "text-left outline-none",
        "focus-visible:rounded-sm focus-visible:outline-2",
        "focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    sidebarHeader: "flex items-center justify-between px-2 py-1",
    sidebarTitle: "text-xs font-semibold uppercase tracking-wider text-fg-muted",
    sidebarCount: "text-xs text-fg-muted",
    sidebarHint: "px-2 py-3 text-sm text-fg-muted",
    sidebarError: "flex flex-col gap-2 p-2 text-sm text-neg-fg",

    conversationList: "flex min-h-0 flex-col gap-1 overflow-y-auto",

    conversationItem: [
        "flex w-full items-center gap-3 rounded-lg",
        "px-3 py-2.5 text-left text-sm text-fg-body",
        "transition-colors hover:bg-muted",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    conversationActive: [
        "flex w-full items-center gap-3 rounded-lg",
        "bg-muted px-3 py-2.5 text-left text-sm font-medium text-fg",
        "focus-visible:outline-2 focus-visible:outline-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    conversationIcon: "size-4 shrink-0 text-fg-muted",
    conversationTitle: "min-w-0 flex-1 truncate",

    chatArea: [
        "flex min-h-0 min-w-0 flex-1 flex-col bg-surface",
    ].join(" "),

    emptyState: [
        "flex min-h-0 flex-1 flex-col items-center justify-center",
        "gap-3 px-6 py-12 text-center",
    ].join(" "),

    emptyIcon: [
        "mb-2 flex size-14 items-center justify-center",
        "rounded-2xl bg-muted",
    ].join(" "),

    emptyIconGraphic: "size-7 text-primary",
    emptyTitle: "text-xl font-semibold tracking-tight text-fg",
    emptyDescription: "max-w-md text-sm leading-6 text-fg-body",

    messages: [
        "flex min-h-0 flex-1 flex-col gap-6",
        "overflow-y-auto px-5 py-6 sm:px-8",
    ].join(" "),

    messageRow: "flex w-full items-start gap-3",
    userMessageRow: "flex w-full justify-end",

    assistantAvatar: [
        "flex size-8 shrink-0 items-center justify-center",
        "rounded-full bg-muted",
    ].join(" "),

    assistantAvatarIcon: "size-4 text-primary",

    userMessage: [
        "w-fit max-w-[85%] rounded-2xl rounded-br-sm",
        "bg-muted px-4 py-3 text-sm text-fg",
        "sm:max-w-[75%]",
    ].join(" "),

    assistantMessage: [
        "min-w-0 max-w-[85%] py-1 text-sm text-fg",
        "sm:max-w-[75%]",
    ].join(" "),

    messageContent: "whitespace-pre-wrap break-words leading-7",
    messageHint: "text-sm text-fg-muted",
    messageError: "flex flex-col items-start gap-3 text-sm text-neg-fg",

    composerWrapper: [
        "shrink-0 border-t border-border",
        "bg-surface px-4 py-4 sm:px-6",
    ].join(" "),

    composer: [
        "mx-auto flex w-full max-w-3xl items-end gap-2",
        "rounded-2xl border border-border bg-muted/30",
        "px-3 py-2 transition-colors",
        "focus-within:border-primary",
    ].join(" "),

    messageInput: [
        "max-h-40 min-h-11 min-w-0 flex-1 resize-none",
        "overflow-y-auto border-none bg-transparent px-2 py-2",
        "text-sm leading-6 text-fg outline-none",
        "placeholder:text-fg-muted",
        "disabled:cursor-not-allowed disabled:opacity-50",
    ].join(" "),

    sendButton: [
        "mb-1 flex !size-9 shrink-0 items-center justify-center",
        "!rounded-xl !p-0",
    ].join(" "),

    sendIcon: "size-4",

    composerHint: [
        "mx-auto mt-2 max-w-3xl",
        "text-center text-[11px] text-fg-muted",
    ].join(" "),

    renameForm: "flex flex-col gap-2",
    renameLabel: "text-sm font-medium text-fg",
};
