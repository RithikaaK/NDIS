import { cn } from '@/lib/utils'

const variants = {
  default:     'bg-purple-800 text-white hover:bg-purple-900 shadow-sm shadow-purple-100 border border-purple-800',
  destructive: 'bg-red-600 text-white hover:bg-red-700 shadow-sm border border-red-600',
  outline:     'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300',
  ghost:       'text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-transparent',
  secondary:   'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-100',
  success:     'bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm border border-emerald-600',
}

const sizes = {
  sm: 'h-7 px-2.5 text-xs gap-1',
  md: 'h-9 px-3.5 text-sm gap-1.5',
  lg: 'h-11 px-5 text-sm gap-2 font-semibold',
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants
  size?: keyof typeof sizes
  children?: React.ReactNode
}

export function Button({
  variant = 'default',
  size = 'md',
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 select-none',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-1',
        'disabled:pointer-events-none disabled:opacity-50',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
