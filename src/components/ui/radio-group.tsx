import * as React from "react"
import * as RadioGroupPrimitive from "@radix-ui/react-radio-group"
import { Circle } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * RadioGroup Module
 * 
 * A fully accessible radio group implementation built on Radix UI primitives.
 * Provides ARIA-compliant radio buttons with comprehensive keyboard navigation
 * and integration with the application's design system.
 * 
 * Key Features:
 * - WAI-ARIA compliance for accessibility
 * - Keyboard navigation support:
 *   • Arrow keys for option selection
 *   • Space to select current option
 *   • Tab for focus management
 * - Seamless design system integration
 * - Form control support with validation
 * - Focus management and visual feedback
 * - Type-safe props and events
 * 
 * @module RadioGroup
 * 
 * @example
 * ```tsx
 * <RadioGroup defaultValue="option1" onValueChange={(value) => console.log(value)}>
 *   <RadioGroupItem value="option1" id="r1">
 *     <Label htmlFor="r1">Option 1</Label>
 *   </RadioGroupItem>
 *   <RadioGroupItem value="option2" id="r2">
 *     <Label htmlFor="r2">Option 2</Label>
 *   </RadioGroupItem>
 * </RadioGroup>
 * ```
 */

/**
 * RadioGroup Props Interface
 * 
 * Extends Radix UI's RadioGroup root props with additional styling options
 * and custom behavior configurations.
 * 
 * @property {string} [className] - Additional CSS classes to apply to the root element
 * @extends {React.ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Root>}
 * 
 * Usage Note:
 * The className prop uses the cn() utility for conditional class merging,
 * allowing dynamic styling based on component state or props.
 */
interface RadioGroupProps extends React.ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Root> {
  className?: string;
}

/**
 * RadioGroup Component
 * Container component for radio options that manages selection state
 * and keyboard interactions.
 */
const RadioGroup = React.forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Root>,
  RadioGroupProps
>(({ className, ...props }, ref) => {
  return (
    <RadioGroupPrimitive.Root
      className={cn("grid gap-2", className)}
      {...props}
      ref={ref}
    />
  )
})
RadioGroup.displayName = RadioGroupPrimitive.Root.displayName

/**
 * RadioGroupItemProps Interface
 * Defines props for individual radio button items within the group.
 */
interface RadioGroupItemProps extends
  React.ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Item> {
  /** Additional CSS classes to apply to the item element */
  className?: string;
}

/** Individual radio button within a RadioGroup */
const RadioGroupItem = React.forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Item>,
  RadioGroupItemProps
>(({ className, ...props }, ref) => (
  <RadioGroupPrimitive.Item
    ref={ref}
    className={cn(
      "aspect-square h-4 w-4 rounded-full border border-primary text-primary",
      "ring-offset-background focus:outline-none focus-visible:ring-2",
      "focus-visible:ring-ring focus-visible:ring-offset-2",
      "disabled:cursor-not-allowed disabled:opacity-50",
      "transition-colors duration-200",
      className
    )}
    {...props}
  >
    <RadioGroupPrimitive.Indicator className="flex items-center justify-center">
      <Circle className="h-2.5 w-2.5 fill-current text-current" />
    </RadioGroupPrimitive.Indicator>
  </RadioGroupPrimitive.Item>
))
RadioGroupItem.displayName = RadioGroupPrimitive.Item.displayName

export { RadioGroup, RadioGroupItem }