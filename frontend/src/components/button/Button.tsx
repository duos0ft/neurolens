import { forwardRef, type ButtonHTMLAttributes } from "react";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../../lib/cn";
import { buttonVariants } from "./Button.styles";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants>;

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant, size, type = "button", ...props }, ref) => {
        return <button ref={ref} type={type} className={cn(buttonVariants({ variant, size }), className)} {...props} />;
    },
);

Button.displayName = "Button";
