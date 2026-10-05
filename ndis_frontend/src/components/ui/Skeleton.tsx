import { cn } from '@/lib/utils'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

/* ─── Base shimmer block ─── */
export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-lg bg-slate-100',
        className,
      )}
      {...props}
    />
  )
}

/* ─── KPI card skeleton (Dashboard) ─── */
export function SkeletonKPI() {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
      <div className="flex items-start justify-between mb-4">
        <Skeleton className="h-11 w-11 rounded-xl" />
        <Skeleton className="h-4 w-4" />
      </div>
      <Skeleton className="h-8 w-16 mb-2" />
      <Skeleton className="h-3 w-24 mb-3" />
      <Skeleton className="h-3 w-20" />
    </div>
  )
}

/* ─── Table row skeleton ─── */
export function SkeletonRow({ cols = 6 }: { cols?: number }) {
  return (
    <tr className="border-b border-slate-50">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-4">
          <Skeleton className={`h-4 ${i === 0 ? 'w-36' : i === cols - 1 ? 'w-12 ml-auto' : 'w-24'}`} />
        </td>
      ))}
    </tr>
  )
}

/* ─── Full table skeleton ─── */
export function SkeletonTable({ rows = 6, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex gap-6">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className={`h-3 ${i === 0 ? 'w-28' : 'w-16'}`} />
        ))}
      </div>
      {/* Rows */}
      <table className="w-full">
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <SkeletonRow key={i} cols={cols} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ─── Card grid skeleton (Roles page) ─── */
export function SkeletonCards({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="h-1.5 bg-slate-100" />
          <div className="p-5 space-y-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-xl" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
            <Skeleton className="h-3 w-full" />
            <div className="flex gap-1.5">
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </div>
            <Skeleton className="h-8 w-full rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  )
}

/* ─── Dashboard skeleton ─── */
export function SkeletonDashboard() {
  return (
    <div className="space-y-6">
      {/* Banner */}
      <Skeleton className="h-36 w-full rounded-2xl" />

      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {[0,1,2,3].map(i => <SkeletonKPI key={i} />)}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity feed */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-4">
          <div className="flex justify-between">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-4 w-16" />
          </div>
          {[0,1,2,3,4].map(i => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-8 w-8 rounded-lg shrink-0" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))}
        </div>

        {/* Right column */}
        <div className="space-y-5">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-3">
            <Skeleton className="h-5 w-28" />
            <div className="grid grid-cols-2 gap-2.5">
              {[0,1,2,3].map(i => <Skeleton key={i} className="h-16 rounded-xl" />)}
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-3">
            <Skeleton className="h-5 w-32" />
            {[0,1,2,3].map(i => (
              <div key={i} className="space-y-1.5">
                <div className="flex justify-between"><Skeleton className="h-3 w-24" /><Skeleton className="h-3 w-10" /></div>
                <Skeleton className="h-1.5 w-full rounded-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Organisation tab skeleton ─── */
export function SkeletonOrgTab() {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
      <div className="flex justify-between mb-5">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-8 w-16 rounded-lg" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[0,1,2,3,4,5,6,7].map(i => (
          <div key={i} className="space-y-1.5">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-5 w-36" />
          </div>
        ))}
      </div>
    </div>
  )
}
