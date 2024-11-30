import * as React from "react"
import { cn } from "@/lib/utils"

/**
 * Input component props interface.
 * Extends native HTML input props with additional styling capabilities.
 * 
 * Features:
 * - Full HTML input compatibility
 * - Type-safe props
 * - Custom class name support
 * - Integration with design system
 * 
 * @interface InputProps
 * @extends {React.InputHTMLAttributes<HTMLInputElement>}
 * 
 * @example
 * ```tsx
 * // Basic usage
 * <Input type="text" placeholder="Enter text" />
 * 
 * // With custom styling
 * <Input className="custom-input" type="email" required />
 * ```
 */
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Custom className for styling overrides, merged with default styles */
  className?: string;
}

/**
 * A foundational input component with design system integration.
 * 
 * Features:
 * - Native input compatibility
 * - Design system styling
 * - WAI-ARIA accessibility
 * - Form validation support
 * - Custom file input styling
 * 
 * @component
 * @example
 * ```tsx
 * // Basic usage
 * <Input type="text" placeholder="Enter your name" />
 * 
 * // With form validation
 * <Input 
 *   aria-invalid={errors.name ? "true" : "false"}
 *   aria-describedby="name-error"
 * />
 * ```
 * 
 * @see {@link FormField} For form integration
 * @see {@link Label} For input labeling
 */
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)

Input.displayName = "Input"

export { Input }
