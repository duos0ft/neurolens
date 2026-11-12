export const dialogStyles = {
    root: [
        "fixed inset-0 m-auto",
        "w-[calc(100%_-_2rem)] max-h-[calc(100dvh_-_2rem)]",
        "overflow-visible rounded-xl border border-border",
        "bg-surface p-0 text-fg shadow-xl",
        "backdrop:bg-black/40",
    ].join(" "),

    sizes: {
        sm: "max-w-sm",
        md: "max-w-lg",
        lg: "max-w-2xl",
        xl: "w-[min(850px,calc(100vw-2rem))] max-w-full",
    },

    content: "flex flex-col text-left",

    header: "flex items-start justify-between gap-4 px-6 pt-6 pb-4 text-left",
    heading: "flex min-w-0 flex-col gap-1",
    title: "text-lg font-semibold tracking-tight text-fg",
    description: "text-sm text-fg-muted",

    body: "px-6 py-4 text-left",

    footer: [
        "flex flex-wrap items-center justify-end gap-2",
        "border-t border-border px-6 py-4",
    ].join(" "),
};
