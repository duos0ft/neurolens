import { forwardRef, type HTMLAttributes } from "react";
import type { VariantProps } from "class-variance-authority";

import { cn } from "../../lib/cn";
import { cardVariants } from "./Card.styles";

export type CardProps = HTMLAttributes<HTMLDivElement> & VariantProps<typeof cardVariants>;

export const Card = forwardRef<HTMLDivElement, CardProps>(({ className, variant, padding, ...props }, ref) => (
    <div ref={ref} className={cn(cardVariants({ variant, padding }), className)} {...props} />
));

Card.displayName = "Card";
