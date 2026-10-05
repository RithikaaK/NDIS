import { cn } from '@/lib/utils'

interface SpinnerProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export function Spinner({ className }: SpinnerProps) {
  return (
    <div className={cn('animate-spin rounded-full border-2 border-muted border-t-primary h-5 w-5', className)} />
  )
}
