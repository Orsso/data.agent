'use client'

/**
 * Radix UI component overrides for BlockNote's @blocknote/shadcn theme.
 *
 * Problem: @blocknote/shadcn has Portal wrappers COMMENTED OUT in its Radix
 * components. Without portals, floating elements (toolbar, menus) render
 * inline and get clipped by ancestor `overflow` containers (our dashboard cards).
 *
 * Solution: Provide complete component groups via the `shadCNComponents` prop.
 * BlockNote does a SHALLOW merge at the group level — providing only the
 * Content component would replace the entire group, losing Root/Trigger/etc.
 * So we must provide every component in each overridden group.
 *
 * The `bn-*` class names come from @blocknote/shadcn/style.css (already loaded).
 * Non-Content components are copied verbatim from BlockNote's source.
 * Content components are identical but with Portal wrappers re-enabled.
 */

import { forwardRef } from 'react'
import * as PopoverPrimitive from '@radix-ui/react-popover'
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'
import * as SelectPrimitive from '@radix-ui/react-select'
import { Check, ChevronDown, ChevronRight, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'

// ─── Popover ────────────────────────────────────────────────────────────────

const Popover = PopoverPrimitive.Root
const PopoverTrigger = PopoverPrimitive.Trigger

const PopoverContent = forwardRef<
  React.ComponentRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = 'center', sideOffset = 4, ...props }, ref) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content
      ref={ref}
      align={align}
      sideOffset={sideOffset}
      className={cn(
        'bn-z-50 bn-w-72 bn-rounded-md bn-border bn-bg-popover bn-p-4 bn-text-popover-foreground bn-shadow-md bn-outline-none data-[state=open]:bn-animate-in data-[state=closed]:bn-animate-out data-[state=closed]:bn-fade-out-0 data-[state=open]:bn-fade-in-0 data-[state=closed]:bn-zoom-out-95 data-[state=open]:bn-zoom-in-95 data-[side=bottom]:bn-slide-in-from-top-2 data-[side=left]:bn-slide-in-from-right-2 data-[side=right]:bn-slide-in-from-left-2 data-[side=top]:bn-slide-in-from-bottom-2',
        className,
      )}
      {...props}
    />
  </PopoverPrimitive.Portal>
))
PopoverContent.displayName = 'PopoverContent'

// ─── DropdownMenu ───────────────────────────────────────────────────────────

const DropdownMenu = DropdownMenuPrimitive.Root
const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger
const DropdownMenuSub = DropdownMenuPrimitive.Sub

const DropdownMenuSubTrigger = forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.SubTrigger>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.SubTrigger> & { inset?: boolean }
>(({ className, inset, children, ...props }, ref) => (
  <DropdownMenuPrimitive.SubTrigger
    ref={ref}
    className={cn(
      'bn-flex bn-cursor-default bn-select-none bn-items-center bn-rounded-sm bn-px-2 bn-py-1.5 bn-text-sm bn-outline-none focus:bn-bg-accent data-[state=open]:bn-bg-accent',
      inset && 'bn-pl-8',
      className,
    )}
    {...props}
  >
    {children}
    <ChevronRight className="bn-ml-auto bn-h-4 bn-w-4" />
  </DropdownMenuPrimitive.SubTrigger>
))
DropdownMenuSubTrigger.displayName = 'DropdownMenuSubTrigger'

const DropdownMenuSubContent = forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.SubContent>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.SubContent>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.SubContent
      ref={ref}
      className={cn(
        'bn-z-50 bn-min-w-[8rem] bn-overflow-hidden bn-rounded-md bn-border bn-bg-popover bn-p-1 bn-text-popover-foreground bn-shadow-lg data-[state=open]:bn-animate-in data-[state=closed]:bn-animate-out data-[state=closed]:bn-fade-out-0 data-[state=open]:bn-fade-in-0 data-[state=closed]:bn-zoom-out-95 data-[state=open]:bn-zoom-in-95 data-[side=bottom]:bn-slide-in-from-top-2 data-[side=left]:bn-slide-in-from-right-2 data-[side=right]:bn-slide-in-from-left-2 data-[side=top]:bn-slide-in-from-bottom-2',
        className,
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
))
DropdownMenuSubContent.displayName = 'DropdownMenuSubContent'

const DropdownMenuContent = forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        'bn-z-50 bn-min-w-[8rem] bn-overflow-hidden bn-rounded-md bn-border bn-bg-popover bn-p-1 bn-text-popover-foreground bn-shadow-md data-[state=open]:bn-animate-in data-[state=closed]:bn-animate-out data-[state=closed]:bn-fade-out-0 data-[state=open]:bn-fade-in-0 data-[state=closed]:bn-zoom-out-95 data-[state=open]:bn-zoom-in-95 data-[side=bottom]:bn-slide-in-from-top-2 data-[side=left]:bn-slide-in-from-right-2 data-[side=right]:bn-slide-in-from-left-2 data-[side=top]:bn-slide-in-from-bottom-2',
        className,
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
))
DropdownMenuContent.displayName = 'DropdownMenuContent'

const DropdownMenuItem = forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item> & { inset?: boolean }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      'bn-relative bn-flex bn-cursor-default bn-select-none bn-items-center bn-rounded-sm bn-px-2 bn-py-1.5 bn-text-sm bn-outline-none bn-transition-colors focus:bn-bg-accent focus:bn-text-accent-foreground data-[disabled]:bn-pointer-events-none data-[disabled]:bn-opacity-50',
      inset && 'bn-pl-8',
      className,
    )}
    {...props}
  />
))
DropdownMenuItem.displayName = 'DropdownMenuItem'

const DropdownMenuCheckboxItem = forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.CheckboxItem>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.CheckboxItem>
>(({ className, children, checked, ...props }, ref) => (
  <DropdownMenuPrimitive.CheckboxItem
    ref={ref}
    className={cn(
      'bn-relative bn-flex bn-cursor-default bn-select-none bn-items-center bn-rounded-sm bn-py-1.5 bn-pl-8 bn-pr-2 bn-text-sm bn-outline-none bn-transition-colors focus:bn-bg-accent focus:bn-text-accent-foreground data-[disabled]:bn-pointer-events-none data-[disabled]:bn-opacity-50',
      className,
    )}
    checked={checked}
    {...props}
  >
    <span className="bn-absolute bn-left-2 bn-flex bn-h-3.5 bn-w-3.5 bn-items-center bn-justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <Check className="bn-h-4 bn-w-4" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.CheckboxItem>
))
DropdownMenuCheckboxItem.displayName = 'DropdownMenuCheckboxItem'

const DropdownMenuLabel = forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Label> & { inset?: boolean }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Label
    ref={ref}
    className={cn(
      'bn-px-2 bn-py-1.5 bn-text-sm bn-font-semibold',
      inset && 'bn-pl-8',
      className,
    )}
    {...props}
  />
))
DropdownMenuLabel.displayName = 'DropdownMenuLabel'

const DropdownMenuSeparator = forwardRef<
  React.ComponentRef<typeof DropdownMenuPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Separator
    ref={ref}
    className={cn('bn--mx-1 bn-my-1 bn-h-px bn-bg-muted', className)}
    {...props}
  />
))
DropdownMenuSeparator.displayName = 'DropdownMenuSeparator'

// ─── Select ─────────────────────────────────────────────────────────────────

const Select = SelectPrimitive.Root
const SelectValue = SelectPrimitive.Value

const SelectTrigger = forwardRef<
  React.ComponentRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      'bn-flex bn-h-10 bn-w-full bn-items-center bn-justify-between bn-rounded-md bn-border bn-border-input bn-bg-background bn-px-3 bn-py-2 bn-text-sm bn-ring-offset-background placeholder:bn-text-muted-foreground focus:bn-outline-none focus:bn-ring-2 focus:bn-ring-ring focus:bn-ring-offset-2 disabled:bn-cursor-not-allowed disabled:bn-opacity-50 [&>span]:bn-line-clamp-1',
      className,
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="bn-h-4 bn-w-4 bn-opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
))
SelectTrigger.displayName = 'SelectTrigger'

const SelectScrollUpButton = forwardRef<
  React.ComponentRef<typeof SelectPrimitive.ScrollUpButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollUpButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollUpButton
    ref={ref}
    className={cn('bn-flex bn-cursor-default bn-items-center bn-justify-center bn-py-1', className)}
    {...props}
  >
    <ChevronUp className="bn-h-4 bn-w-4" />
  </SelectPrimitive.ScrollUpButton>
))
SelectScrollUpButton.displayName = 'SelectScrollUpButton'

const SelectScrollDownButton = forwardRef<
  React.ComponentRef<typeof SelectPrimitive.ScrollDownButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollDownButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollDownButton
    ref={ref}
    className={cn('bn-flex bn-cursor-default bn-items-center bn-justify-center bn-py-1', className)}
    {...props}
  >
    <ChevronDown className="bn-h-4 bn-w-4" />
  </SelectPrimitive.ScrollDownButton>
))
SelectScrollDownButton.displayName = 'SelectScrollDownButton'

const SelectContent = forwardRef<
  React.ComponentRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = 'popper', ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        'bn-relative bn-z-50 bn-max-h-96 bn-min-w-[8rem] bn-overflow-hidden bn-rounded-md bn-border bn-bg-popover bn-text-popover-foreground bn-shadow-md data-[state=open]:bn-animate-in data-[state=closed]:bn-animate-out data-[state=closed]:bn-fade-out-0 data-[state=open]:bn-fade-in-0 data-[state=closed]:bn-zoom-out-95 data-[state=open]:bn-zoom-in-95 data-[side=bottom]:bn-slide-in-from-top-2 data-[side=left]:bn-slide-in-from-right-2 data-[side=right]:bn-slide-in-from-left-2 data-[side=top]:bn-slide-in-from-bottom-2',
        position === 'popper' &&
          'data-[side=bottom]:bn-translate-y-1 data-[side=left]:bn--translate-x-1 data-[side=right]:bn-translate-x-1 data-[side=top]:bn--translate-y-1',
        className,
      )}
      position={position}
      {...props}
    >
      <SelectScrollUpButton />
      <SelectPrimitive.Viewport
        className={cn(
          'bn-p-1',
          position === 'popper' &&
            'bn-h-[var(--radix-select-trigger-height)] bn-w-full bn-min-w-[var(--radix-select-trigger-width)]',
        )}
      >
        {children}
      </SelectPrimitive.Viewport>
      <SelectScrollDownButton />
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
))
SelectContent.displayName = 'SelectContent'

const SelectItem = forwardRef<
  React.ComponentRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      'bn-relative bn-flex bn-w-full bn-cursor-default bn-select-none bn-items-center bn-rounded-sm bn-py-1.5 bn-pl-8 bn-pr-2 bn-text-sm bn-outline-none focus:bn-bg-accent focus:bn-text-accent-foreground data-[disabled]:bn-pointer-events-none data-[disabled]:bn-opacity-50',
      className,
    )}
    {...props}
  >
    <span className="bn-absolute bn-left-2 bn-flex bn-h-3.5 bn-w-3.5 bn-items-center bn-justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="bn-h-4 bn-w-4" />
      </SelectPrimitive.ItemIndicator>
    </span>
    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
))
SelectItem.displayName = 'SelectItem'

// ─── Export ─────────────────────────────────────────────────────────────────

/**
 * Pass to <BlockNoteView shadCNComponents={portaledShadCNComponents}>
 *
 * BlockNote merges this with its defaults via shallow spread at the group level:
 *   { ...ShadCNDefaultComponents, ...shadCNComponents }
 *
 * So each group must be COMPLETE — partial groups would lose unspecified components.
 * Only groups that need Portal overrides are included; other groups (Button,
 * Card, Tabs, etc.) fall through to BlockNote's defaults.
 *
 * The `any` cast is required because the TS type is not exported from @blocknote/shadcn.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const portaledShadCNComponents: any = {
  Popover: {
    Popover,
    PopoverContent,
    PopoverTrigger,
  },
  DropdownMenu: {
    DropdownMenu,
    DropdownMenuCheckboxItem,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuSub,
    DropdownMenuSubContent,
    DropdownMenuSubTrigger,
    DropdownMenuTrigger,
  },
  Select: {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
  },
}
