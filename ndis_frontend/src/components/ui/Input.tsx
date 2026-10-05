import { cn } from '@/lib/utils'

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  /** Field-level error message. When set, the input gets a red ring and the
   * message renders directly below it — this is the single consistent way
   * field errors (backend or client-side) should be shown across the app. */
  error?: string | null
}

export function Input({ className, error, ...props }: InputProps) {
  // Fragment, not a wrapping <div> — keeps this a drop-in replacement with no
  // layout/box changes wherever Input is already used in flex rows or grids.
  return (
    <>
      <input
        aria-invalid={!!error}
        className={cn(
          'flex h-9 w-full rounded-lg border bg-slate-50 px-3 text-sm',
          'placeholder:text-slate-400 text-slate-900',
          'focus:outline-none focus:ring-2 focus:border-transparent focus:bg-white',
          error
            ? 'border-red-300 focus:ring-red-400 bg-red-50'
            : 'border-slate-200 focus:ring-purple-500',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'transition-all duration-150',
          className,
        )}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </>
  )
}
