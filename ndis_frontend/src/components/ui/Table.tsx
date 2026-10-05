import { cn } from '@/lib/utils'

interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  className?: string
  children?: React.ReactNode
}

interface TableSectionProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  children?: React.ReactNode
}

interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  className?: string
  children?: React.ReactNode
}

interface TableCellProps extends React.TdHTMLAttributes<HTMLTableCellElement> {
  className?: string
  children?: React.ReactNode
}

interface TableHeadProps extends React.ThHTMLAttributes<HTMLTableCellElement> {
  className?: string
  children?: React.ReactNode
}

export function Table({ className, children, ...props }: TableProps) {
  return (
    <div className="w-full overflow-auto">
      <table className={cn('w-full text-sm border-collapse', className)} {...props}>
        {children}
      </table>
    </div>
  )
}

export function TableHeader({ children, ...props }: TableSectionProps) {
  return <thead className="bg-slate-50 border-b border-slate-100" {...props}>{children}</thead>
}

export function TableBody({ children, ...props }: TableSectionProps) {
  return <tbody className="divide-y divide-slate-50" {...props}>{children}</tbody>
}

export function TableRow({ className, children, ...props }: TableRowProps) {
  return (
    <tr
      className={cn('data-row', className)}
      {...props}
    >
      {children}
    </tr>
  )
}

export function TableHead({ className, children, ...props }: TableHeadProps) {
  return (
    <th
      className={cn(
        'px-4 py-3 text-left text-[11px] font-bold text-slate-500 uppercase tracking-wider whitespace-nowrap',
        className,
      )}
      {...props}
    >
      {children}
    </th>
  )
}

export function TableCell({ className, children, ...props }: TableCellProps) {
  return (
    <td className={cn('px-4 py-3.5 text-slate-700 text-sm', className)} {...props}>
      {children}
    </td>
  )
}
