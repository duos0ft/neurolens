export const chatMessageContentStyles = {
    root: [
        "min-w-0 break-words",
        "text-sm leading-7 text-fg",
        "[&>*:first-child]:mt-0",
        "[&>*:last-child]:mb-0",
    ].join(" "),

    heading: [
        "mb-3 mt-7",
        "text-base font-semibold leading-6",
        "tracking-tight text-fg",
    ].join(" "),

    subheading: [
        "mb-3 mt-6",
        "text-sm font-semibold leading-6",
        "text-fg",
    ].join(" "),

    paragraph: [
        "mb-4 whitespace-pre-wrap",
        "leading-7 text-fg-body",
    ].join(" "),

    unorderedList: [
        "my-4 list-disc space-y-3 pl-6",
        "text-fg-body",
    ].join(" "),

    orderedList: [
        "my-4 list-decimal space-y-3 pl-6",
        "text-fg-body",
    ].join(" "),

    listItem: [
        "pl-1 leading-7",
    ].join(" "),

    blockquote: [
        "my-5 border-l-2 border-border-strong",
        "pl-4 italic text-fg-muted",
    ].join(" "),

    strong: [
        "font-semibold text-fg",
    ].join(" "),

    link: [
        "font-medium text-fg underline",
        "underline-offset-4",
        "transition-colors hover:text-accent",
        "focus-visible:outline-2",
        "focus-visible:outline-border-strong",
    ].join(" "),

    code: [
        "rounded-md bg-muted px-1.5 py-0.5",
        "font-mono text-xs text-fg",
    ].join(" "),

    citationLink: [
        "inline-flex items-center rounded-md",
        "bg-accent-soft px-1.5 py-0.5",
        "text-xs font-semibold text-accent",
        "no-underline transition-colors",
        "hover:bg-muted",
        "focus-visible:outline-2",
        "focus-visible:outline-border-strong",
    ].join(" "),
};
