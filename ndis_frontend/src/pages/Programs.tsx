import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { SlideOver } from '@/components/ui/SlideOver'
import { SkeletonTable } from '@/components/ui/Skeleton'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table'
import { useAuth } from '@/context/AuthContext'
import { getPrograms, createProgram, updateProgram } from '@/api/programs'
import { Plus, Search, Edit2, BookOpen } from 'lucide-react'

const PROGRAM_TYPES = [
  'Support Coordination', 'Daily Activities', 'Community Access',
  'Therapy', 'Accommodation', 'Employment', 'Behaviour Support', 'Other',
]
const TYPE_COLORS = {
  'Support Coordination': 'default', 'Daily Activities': 'info',
  'Community Access': 'success', 'Therapy': 'warning',
  'Accommodation': 'secondary', 'Employment': 'outline',
  'Behaviour Support': 'destructive',
}
const empty = { program_name: '', program_code: '', program_type: 'Support Coordination', description: '', is_active: true }
const inputCls = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const selectCls = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const labelCls = "text-xs font-semibold text-slate-600 uppercase tracking-wide"

export default function Programs() {
  const { user } = useAuth()
  const tenantId = user?.tenant_id
  const queryClient = useQueryClient()

  const [search, setSearch]       = useState('')
  const [slideOpen, setSlideOpen] = useState(false)
  const [editing, setEditing]     = useState(null)
  const [form, setForm]           = useState(empty)
  const [toast, setToast]         = useState('')

  const flash = (m) => { setToast(m); setTimeout(() => setToast(''), 3000) }
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['programs', tenantId] })

  const { data: programs = [], isLoading } = useQuery({
    queryKey: ['programs', tenantId],
    queryFn: () => getPrograms(tenantId).then(r => r.data || []),
    enabled: !!tenantId,
  })

  const saveMut = useMutation({
    mutationFn: (payload: any) => editing
      ? updateProgram(tenantId, editing.id, payload)
      : createProgram(tenantId, payload),
    onSuccess: () => { invalidate(); setSlideOpen(false); flash('Program saved successfully.') },
    onError:   () => flash('Failed to save program.'),
  })

  const openNew  = () => { setEditing(null); setForm(empty); setSlideOpen(true) }
  const openEdit = (p) => { setEditing(p); setForm({ ...p }); setSlideOpen(true) }
  const save     = () => saveMut.mutate(form)

  const filtered = programs.filter(p =>
    `${p.program_name} ${p.program_type} ${p.program_code}`.toLowerCase().includes(search.toLowerCase())
  )
  const activeCount   = programs.filter(p => p.is_active).length
  const inactiveCount = programs.length - activeCount

  return (
    <Layout title="Programs">
      <div className="space-y-5 animate-fade-in">
        {toast && (
          <div className="fixed top-5 right-5 z-50 bg-slate-900 text-white text-sm px-4 py-3 rounded-xl shadow-xl animate-fade-in flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />{toast}
          </div>
        )}

        {/* Stats strip */}
        {!isLoading && programs.length > 0 && (
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Total Programs', value: programs.length, color: 'text-purple-600 bg-purple-50' },
              { label: 'Active',         value: activeCount,     color: 'text-emerald-600 bg-emerald-50' },
              { label: 'Inactive',       value: inactiveCount,   color: 'text-slate-600 bg-slate-100' },
            ].map(({ label, value, color }) => (
              <div key={label} className={`rounded-xl px-4 py-3 ${color} flex items-center justify-between`}>
                <span className="text-sm font-medium opacity-80">{label}</span>
                <span className="text-2xl font-bold">{value}</span>
              </div>
            ))}
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold text-slate-900">Programs</h1>
            <p className="text-sm text-slate-400 mt-0.5">Manage your NDIS support programs and services</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <Input placeholder="Search programs..." className="pl-8 w-56" value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <Button onClick={openNew}><Plus className="h-4 w-4" /> Add Program</Button>
          </div>
        </div>

        {isLoading ? (
          <SkeletonTable rows={5} cols={6} />
        ) : (
          <Card>
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="h-16 w-16 rounded-2xl bg-purple-50 flex items-center justify-center mb-4">
                  <BookOpen className="h-8 w-8 text-purple-400" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-1">{search ? 'No programs found' : 'No programs yet'}</h3>
                <p className="text-sm text-slate-400 max-w-xs mb-5">
                  {search ? `No results for "${search}".` : 'Create your first NDIS support program.'}
                </p>
                {!search && <Button onClick={openNew}><Plus className="h-4 w-4" /> Add Program</Button>}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Program</TableHead>
                    <TableHead>Code</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map(p => (
                    <TableRow key={p.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
                            <BookOpen className="h-4 w-4 text-purple-500" />
                          </div>
                          <span className="font-semibold text-slate-900">{p.program_name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-mono">{p.program_code || '—'}</code>
                      </TableCell>
                      <TableCell>
                        <Badge variant={TYPE_COLORS[p.program_type] || 'secondary'}>{p.program_type}</Badge>
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm max-w-xs">
                        <span className="line-clamp-1">{p.description || <span className="text-slate-300">—</span>}</span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={p.is_active ? 'success' : 'secondary'}>
                          <span className={`h-1.5 w-1.5 rounded-full ${p.is_active ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                          {p.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button size="sm" variant="ghost" onClick={() => openEdit(p)}>
                          <Edit2 className="h-3.5 w-3.5" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        )}
      </div>

      <SlideOver open={slideOpen} onClose={() => setSlideOpen(false)}
        title={editing ? 'Edit Program' : 'Add Program'}
        subtitle={editing ? `Editing ${editing.program_name}` : 'Fill in the program details below'}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className={labelCls}>Program Name *</label>
            <input className={inputCls} value={form.program_name} onChange={e => setForm({ ...form, program_name: e.target.value })} placeholder="Daily Living Support" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className={labelCls}>Program Code</label>
              <input className={inputCls} value={form.program_code} onChange={e => setForm({ ...form, program_code: e.target.value })} placeholder="DLS-01" />
            </div>
            <div className="space-y-1.5">
              <label className={labelCls}>Program Type</label>
              <select className={selectCls} value={form.program_type} onChange={e => setForm({ ...form, program_type: e.target.value })}>
                {PROGRAM_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className={labelCls}>Description</label>
            <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={3} placeholder="Brief description of this program..."
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white resize-none transition-all" />
          </div>
          {editing && (
            <div className="flex items-center gap-2 py-1">
              <input type="checkbox" id="prog-active" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} className="h-4 w-4 rounded border-slate-300" />
              <label htmlFor="prog-active" className="text-sm font-medium text-slate-700">Active</label>
            </div>
          )}
          <div className="flex gap-3 pt-4 border-t border-slate-100">
            <Button className="flex-1" onClick={save} disabled={saveMut.isPending || !form.program_name}>
              {saveMut.isPending && <svg className="animate-spin h-3.5 w-3.5 mr-1.5" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>}
              {saveMut.isPending ? 'Saving...' : editing ? 'Update Program' : 'Add Program'}
            </Button>
            <Button variant="outline" onClick={() => setSlideOpen(false)}>Cancel</Button>
          </div>
        </div>
      </SlideOver>
    </Layout>
  )
}
