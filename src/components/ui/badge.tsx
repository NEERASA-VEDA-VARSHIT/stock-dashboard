import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "bg-cyan-100 text-cyan-900 dark:bg-cyan-900/40 dark:text-cyan-200",
        success: "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-200",
        danger: "bg-rose-100 text-rose-900 dark:bg-rose-900/40 dark:text-rose-200",
        warning: "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-200",
        secondary: "bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-slate-200",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
