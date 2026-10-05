import { cn } from '@/lib/utils'

const variants = {
  default:     'bg-purple-50 text-purple-700 border border-purple-200/80',
  secondary:   'bg-slate-100 text-slate-600 border border-slate-200',
  destructive: 'bg-red-50 text-red-700 border border-red-200/80',
  outline:     'border border-slate-200 text-slate-600 bg-transparent',
  success:     'bg-emerald-50 text-emerald-700 border border-emerald-200/80',
  warning:     'bg-amber-50 text-amber-700 border border-amber-200/80',
  info:        'bg-sky-50 text-sky-700 border border-sky-200/80',
}

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children?: React.ReactNode
  variant?: keyof typeof variants
  className?: string
}

export function Badge({ variant = 'default', className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold leading-none',
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}
