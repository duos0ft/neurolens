export const chatMessageContentStyles = {
    root: [
        "min-w-0 break-words",
        "text-sm leading-7 text-slate-800",
        "[&>*:first-child]:mt-0",
        "[&>*:last-child]:mb-0",
    ].join(" "),

    heading: [
        "mb-3 mt-6 text-base font-semibold",
        "tracking-tight text-slate-950",
    ].join(" "),

    subheading: [
        "mb-2 mt-5 text-sm font-semibold",
        "text-slate-900",
    ].join(" "),

    paragraph: "mb-3 whitespace-pre-wrap",

    unorderedList: "mb-4 list-disc space-y-1.5 pl-5",

    orderedList: "mb-4 list-decimal space-y-1.5 pl-5",

    listItem: "pl-1 leading-7",

    blockquote: [
        "my-4 border-l-2 border-slate-300",
        "pl-4 italic text-slate-600",
    ].join(" "),

    strong: "font-semibold text-slate-950",

    link: [
        "font-medium text-slate-800 underline",
        "underline-offset-4 hover:text-slate-950",
    ].join(" "),

    code: [
        "rounded-md bg-slate-100 px-1.5 py-0.5",
        "font-mono text-xs text-slate-900",
    ].join(" "),
};
