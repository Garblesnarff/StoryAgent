import * as React from "react"
import { cn } from "@/lib/utils"

/**
 * TextareaProps Interface
 * Extends the standard HTML textarea element props while maintaining
 * full compatibility with native textarea attributes.
 * 
 * @interface TextareaProps
 * @extends {React.TextareaHTMLAttributes<HTMLTextAreaElement>}
 */
export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

/**
 * Textarea Component
 * 
 * A reusable textarea component that provides consistent styling and behavior
 * across the application. This component enhances the native textarea element
 * with the application's design system.
 * 
 * Features:
 * - Minimum height constraint
 * - Consistent border and focus states
 * - Responsive width
 * - Custom styling support
 * - Proper disabled state handling
 * - Accessible by default
 * 
 * @component
 * @example
 * ```tsx
 * // Basic usage
 * <Textarea placeholder="Enter your message" />
 * 
 * // With custom height
 * <Textarea className="min-h-[200px]" />
 * 
 * // As a controlled component
 * <Textarea
 *   value={value}
 *   onChange={(e) => setValue(e.target.value)}
 *   placeholder="Type your story..."
 * />
 * ```
 */
const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)

Textarea.displayName = "Textarea"

export { Textarea }
