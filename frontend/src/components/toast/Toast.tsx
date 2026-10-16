import { Toaster as SonnerToaster, type ToasterProps } from "sonner";

export type ToastProps = Pick<ToasterProps, "position" | "duration" | "visibleToasts" | "expand">;

export function Toast({
    position = "top-right",
    duration = 4000,
    visibleToasts = 4,
    expand = false,
}: ToastProps) {
    return (
        <SonnerToaster
            position={position}
            duration={duration}
            visibleToasts={visibleToasts}
            expand={expand}
            closeButton
            richColors={false}
            toastOptions={{
                classNames: {
                    toast: "rounded-md! border! border-border! bg-surface! text-fg! shadow-popover!",
                    title: "font-medium! text-fg!",
                    description: "text-fg-muted!",
                    closeButton: "border-border! bg-surface! text-fg!",
                    success: "border-l-4! border-l-pos-fg!",
                    error: "border-l-4! border-l-neg-fg!",
                    warning: "border-l-4! border-l-amber-500!",
                    info: "border-l-4! border-l-accent!",
                },
            }}
        />
    );
}
