import { useState } from "react";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../../lib/cn";
import { avatarVariants } from "./Avatar.styles";

type AvatarProps = {
    name?: string | null;
    src?: string | null;
    className?: string;
} & VariantProps<typeof avatarVariants>;

function getInitials(name?: string | null): string {
    if (!name?.trim()) {
        return "?";
    }

    const parts = name.trim().split(/\s+/);

    if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase();
    }

    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function Avatar({ name, src, size, className }: AvatarProps) {
    const [ failedSrc, setFailedSrc ] = useState<string | null>(null);
    const showImage = Boolean(src && src !== failedSrc);

    return (
        <span className={cn(avatarVariants({ size }), className)} aria-label={name || "User avatar"}>
            {showImage ? (
                <img src={src!} alt="" className="size-full object-cover" onError={() => setFailedSrc(src ?? null)} />
            ) : (
                <span aria-hidden="true">{getInitials(name)}</span>
            )}
        </span>
    );
}
