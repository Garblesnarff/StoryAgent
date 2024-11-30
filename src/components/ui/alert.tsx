/**
 * Alert Component
 * 
 * An accessible alert dialog system built on Radix UI's AlertDialog primitive.
 * Provides modal dialogs for important messages, warnings, and confirmations.
 * 
 * Features:
 * - ARIA compliant accessibility
 * - Animated transitions
 * - Backdrop blur effect
 * - Responsive design
 * - Keyboard navigation
 * 
 * @module components/ui/alert
 */

import * as React from "react"
import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog"

import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

/**
 * Root alert component that manages the dialog's open state
 */
const Alert = AlertDialogPrimitive.Root

/**
 * Button that triggers the alert dialog
 */
const AlertTrigger = AlertDialogPrimitive.Trigger

/** Portal for rendering alert outside of parent DOM hierarchy */
const AlertPortal = AlertDialogPrimitive.Portal

/**
 * Semi-transparent overlay behind the alert dialog
 * Provides visual focus and prevents interaction with background
 */
const AlertOverlay = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Overlay
    className={cn(
      "fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
    ref={ref}
  />
))
AlertOverlay.displayName = AlertDialogPrimitive.Overlay.displayName

/**
 * Alert Content Container
 * 
 * Main container component that handles the positioning and animation
 * of the alert dialog content.
 * 
 * Features:
 * - Centered modal positioning
 * - Responsive width constraints
 * - Enter/exit animations with zoom and fade
 * - Focus trap for accessibility
 * - Responsive padding and spacing
 * 
 * @component
 * @example
 * ```tsx
 * <Alert>
 *   <AlertContent>
 *     <AlertTitle>Confirmation</AlertTitle>
 *     <AlertDescription>Are you sure?</AlertDescription>
 *   </AlertContent>
 * </Alert>
 * ```
 */
const AlertContent = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Content>
>(({ className, ...props }, ref) => (
  <AlertPortal>
    <AlertOverlay />
    <AlertDialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
        className
      )}
      {...props}
    />
  </AlertPortal>
))
AlertContent.displayName = AlertDialogPrimitive.Content.displayName

const AlertHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col space-y-2 text-center sm:text-left",
      className
    )}
    {...props}
  />
)
AlertHeader.displayName = "AlertHeader"

const AlertTitle = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold", className)}
    {...props}
  />
))
AlertTitle.displayName = AlertDialogPrimitive.Title.displayName

const AlertDescription = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
AlertDescription.displayName = AlertDialogPrimitive.Description.displayName

const AlertFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className
    )}
    {...props}
  />
)
AlertFooter.displayName = "AlertFooter"

const AlertAction = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Action>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Action>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Action
    ref={ref}
    className={cn(buttonVariants(), className)}
    {...props}
  />
))
AlertAction.displayName = AlertDialogPrimitive.Action.displayName

const AlertCancel = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Cancel>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Cancel>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Cancel
    ref={ref}
    className={cn(
      buttonVariants({ variant: "outline" }),
      "mt-2 sm:mt-0",
      className
    )}
    {...props}
  />
))
AlertCancel.displayName = AlertDialogPrimitive.Cancel.displayName

export {
  Alert,
  AlertTrigger,
  AlertContent,
  AlertHeader,
  AlertTitle,
  AlertDescription,
  AlertFooter,
  AlertAction,
  AlertCancel,
}
