import { cn } from '@/lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
  className?: string
}

export function Card({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn('bg-white rounded-2xl border border-slate-100 shadow-sm', className)}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children, ...props }: CardProps) {
  return (
    <div className={cn('px-5 py-4 border-b border-slate-100 flex flex-col gap-1', className)} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({ className, children, ...props }: CardProps) {
  return (
    <h3 className={cn('font-bold text-slate-900 text-sm leading-tight', className)} {...props}>
      {children}
    </h3>
  )
}

export function CardDescription({ className, children, ...props }: CardProps) {
  return (
    <p className={cn('text-xs text-slate-400', className)} {...props}>
      {children}
    </p>
  )
}

export function CardContent({ className, children, ...props }: CardProps) {
  return (
    <div className={cn('px-5 py-4', className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({ className, children, ...props }: CardProps) {
  return (
    <div className={cn('px-5 py-3 border-t border-slate-100', className)} {...props}>
      {children}
    </div>
  )
}
