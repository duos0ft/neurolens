import { forwardRef, type InputHTMLAttributes } from "react";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../../lib/cn";
import { inputVariants } from "./Input.styles";

export type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "size"> & VariantProps<typeof inputVariants>;

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ className, inputSize, type = "text", ...props }, ref) => {
        return <input ref={ref} type={type} className={cn(inputVariants({ inputSize }), className)} {...props} />;
    },
);

Input.displayName = "Input";
