import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { SkeletonOrgTab } from '@/components/ui/Skeleton'
import { useAuth } from '@/context/AuthContext'
import {
  getTenant, updateTenant,
  getConfig, updateConfig,
  getContacts, createContact, updateContact,
  getAddresses, createAddress, updateAddress,
} from '@/api/tenant'
import {
  getDocuments, createDocument, updateDocument, deleteDocument,
} from '@/api/documents'
import {
  Building2, Phone, MapPin, FileText, Clock,
  Plus, Edit2, Save, X,
  Upload, Download, Trash2, File, AlertTriangle, CheckCircle, XCircle,
} from 'lucide-react'

// ── Tab configuration ─────────────────────────────────────────────────────────
const TABS = [
  { id: 'general',   label: 'Organisation Info',    icon: Building2 },
  { id: 'abn',       label: 'ABN & NDIS',           icon: FileText  },
  { id: 'contacts',  label: 'Contacts & Addresses', icon: Phone     },
  { id: 'expiry',    label: 'Expiry Tracking',      icon: Clock     },
  { id: 'documents', label: 'Documents',            icon: MapPin    },
]

const STATES       = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT']
const MAX_FILE_MB  = 5
const ACCEPTED     = '.pdf,.doc,.docx,.png,.jpg,.jpeg'
const selectCls    = 'h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400'
const fieldLabel   = 'text-xs font-medium text-slate-500 uppercase tracking-wide'

const TZ_LABELS: Record<string, string> = {
  'Australia/Sydney':    'Sydney (AEST)',
  'Australia/Melbourne': 'Melbourne (AEST)',
  'Australia/Brisbane':  'Brisbane (AEST)',
  'Australia/Perth':     'Perth (AWST)',
  'Australia/Adelaide':  'Adelaide (ACST)',
  'Australia/Darwin':    'Darwin (ACST)',
  'Australia/Hobart':    'Hobart (AEST)',
}

// ── Sample fallback (shown when API hasn't loaded yet) ────────────────────────
const SAMPLE_TENANT = {
  organisation_name:        'Sunshine Care Pty Ltd',
  trading_name:             '',
  organisation_type:        'Company',
  abn:                      '51 824 753 921',
  acn:                      '824753921',
  ndis_registration_number: '4050012345',
  registration_expiry_date: null,
  is_registered_provider:   true,
  primary_email:            'admin@sunshinecare.com.au',
  primary_phone:            '(02) 9876 5432',
  website_url:              'https://www.sunshinecare.com.au',
  timezone:                 'Australia/Sydney',
  status:                   'Active',
  provider_type:            'Registered',
}

// ── Utility helpers ───────────────────────────────────────────────────────────
function expiryStatus(expiryDateStr: string | null | undefined) {
  if (!expiryDateStr) return { label: 'Not set', color: 'text-slate-400', bg: 'bg-slate-100', days: null }
  const today  = new Date(); today.setHours(0, 0, 0, 0)
  const expiry = new Date(expiryDateStr)
  const days   = Math.round((expiry.getTime() - today.getTime()) / 86400000)
  if (days < 0)   return { label: 'Expired',        color: 'text-red-600',    bg: 'bg-red-100',    days }
  if (days <= 90) return { label: `${days} days`,   color: 'text-amber-600',  bg: 'bg-amber-100',  days }
  return              { label: `${days} days`,       color: 'text-emerald-600', bg: 'bg-emerald-100', days }
}

function docExpiryStatus(expiryDateStr: string | null | undefined) {
  if (!expiryDateStr) return 'active'
  const days = Math.round((new Date(expiryDateStr).getTime() - Date.now()) / 86400000)
  if (days < 0)   return 'expired'
  if (days <= 90) return 'expiring'
  return 'valid'
}

function StatusPill({ status }: { status: string }) {
  if (status === 'expired')  return <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-100 text-red-700">Expired</span>
  if (status === 'expiring') return <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Expiring soon</span>
  if (status === 'valid')    return <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">Valid</span>
  return <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">Active</span>
}

const DOC_LINKED_OPTIONS = [
  '', 'NDIS Registration', 'ABN Registration', 'Insurance – Public Liability',
  'Insurance – Professional Indemnity', 'Insurance – Workers Compensation',
  'Working With Children Check', 'NDIS Quality Audit', 'Organisation Policy', 'Other',
]

const DOC_CATEGORIES = ['Registration', 'Insurance', 'Certificates', 'Policies', 'Compliance', 'Finance', 'HR', 'Other']

export default function Organisation() {
  const { user } = useAuth()
  const tenantId    = user?.tenant_id
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [activeTab,        setActiveTab]        = useState('general')
  const [editMode,         setEditMode]         = useState(false)
  const [abnEditMode,      setAbnEditMode]      = useState(false)
  const [form,             setForm]             = useState<any>({})
  const [abnForm,          setAbnForm]          = useState<any>({})
  const [showAddContact,   setShowAddContact]   = useState(false)
  const [showAddAddress,   setShowAddAddress]   = useState(false)
  const [newContact,       setNewContact]       = useState({ first_name: '', last_name: '', position_title: '', contact_type: 'Primary', email: '', phone: '' })
  const [newAddress,       setNewAddress]       = useState({ address_type: 'Business', address_line1: '', suburb: '', state_code: 'NSW', postcode: '' })
  const [editContactId,    setEditContactId]    = useState<number | null>(null)
  const [editContactForm,  setEditContactForm]  = useState<any>({})
  const [editAddressId,    setEditAddressId]    = useState<number | null>(null)
  const [editAddressForm,  setEditAddressForm]  = useState<any>({})
  const [msg,              setMsg]              = useState('')
  const [docFilter,        setDocFilter]        = useState('All')
  const [fileError,        setFileError]        = useState('')
  const [showUploadModal,  setShowUploadModal]  = useState(false)
  const [uploadFile,       setUploadFile]       = useState<File | null>(null)
  const [uploadForm,       setUploadForm]       = useState({
    name: '', category: 'Registration', categoryOther: '', linked_to: '', expiry: '',
  })

  const flash     = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 3500) }
  const invalidate = (key: string) => queryClient.invalidateQueries({ queryKey: [key, tenantId] })

  // ── Queries ────────────────────────────────────────────────────────────────
  const { data: tenantRaw, isLoading } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn:  () => getTenant(tenantId).then(r => r.data),
    enabled:  !!tenantId,
  })
  const { data: configRaw } = useQuery({
    queryKey: ['config', tenantId],
    queryFn:  () => getConfig(tenantId).then(r => r.data),
    enabled:  !!tenantId,
  })
  const { data: contactsRaw = [] } = useQuery({
    queryKey: ['contacts', tenantId],
    queryFn:  () => getContacts(tenantId).then(r => r.data || []),
    enabled:  !!tenantId,
  })
  const { data: addressesRaw = [] } = useQuery({
    queryKey: ['addresses', tenantId],
    queryFn:  () => getAddresses(tenantId).then(r => r.data || []),
    enabled:  !!tenantId,
  })
  const { data: docsRaw = [] } = useQuery({
    queryKey: ['documents', tenantId],
    queryFn:  () => getDocuments(tenantId!).then(r => r.data || []),
    enabled:  !!tenantId && activeTab === 'documents',
  })

  const tenant   = tenantRaw
    ? { ...SAMPLE_TENANT, ...tenantRaw, ...(configRaw ? { default_funding_type: configRaw.default_funding_type } : {}) }
    : SAMPLE_TENANT
  const contacts  = contactsRaw
  const addresses = addressesRaw
  const docs      = docsRaw as any[]

  const formData    = editMode    ? form    : tenant
  const abnFormData = abnEditMode ? abnForm : tenant

  // ── Mutations ──────────────────────────────────────────────────────────────
  const saveConfigMut = useMutation({
    mutationFn: (payload: any) => updateConfig(tenantId, payload),
    onSuccess:  () => queryClient.invalidateQueries({ queryKey: ['config', tenantId] }),
  })

  const saveTenantMut = useMutation({
    mutationFn: (payload: any) => updateTenant(tenantId, payload),
    onSuccess: (response) => {
      queryClient.setQueryData(['tenant', tenantId], { ...response.data, ...form })
      queryClient.invalidateQueries({ queryKey: ['tenant', tenantId] })
      setEditMode(false)
      setAbnEditMode(false)
      flash('Organisation updated.')
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      flash(typeof detail === 'string' ? detail
        : Array.isArray(detail) ? detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join(' | ')
        : 'Failed to save.')
    },
  })

  const apiErr = (err: any, fallback: string) => {
    const d = err?.response?.data?.detail
    return typeof d === 'string' ? d : fallback
  }

  const addContactMut = useMutation({
    mutationFn: (p: any) => createContact(tenantId, p),
    onSuccess: () => {
      invalidate('contacts'); setShowAddContact(false)
      setNewContact({ first_name: '', last_name: '', position_title: '', contact_type: 'Primary', email: '', phone: '' })
      flash('Contact added.')
    },
    onError: (e: any) => flash(apiErr(e, 'Failed to add contact.')),
  })

  const addAddressMut = useMutation({
    mutationFn: (p: any) => createAddress(tenantId, p),
    onSuccess: () => {
      invalidate('addresses'); setShowAddAddress(false)
      setNewAddress({ address_type: 'Business', address_line1: '', suburb: '', state_code: 'NSW', postcode: '' })
      flash('Address added.')
    },
    onError: (e: any) => flash(apiErr(e, 'Failed to add address.')),
  })

  const updateContactMut = useMutation({
    mutationFn: ({ id, data }: any) => updateContact(tenantId, id, data),
    onSuccess:  () => { invalidate('contacts'); setEditContactId(null); flash('Contact updated.') },
    onError:    (e: any) => flash(apiErr(e, 'Failed to update contact.')),
  })

  const updateAddressMut = useMutation({
    mutationFn: ({ id, data }: any) => updateAddress(tenantId, id, data),
    onSuccess:  () => { invalidate('addresses'); setEditAddressId(null); flash('Address updated.') },
    onError:    (e: any) => flash(apiErr(e, 'Failed to update address.')),
  })

  const createDocMut = useMutation({
    mutationFn: (p: any) => createDocument(tenantId!, p),
    onSuccess:  () => { invalidate('documents'); flash('Document uploaded.') },
    onError:    (e: any) => flash(apiErr(e, 'Failed to upload document.')),
  })

  const deleteDocMut = useMutation({
    mutationFn: (id: number) => deleteDocument(tenantId!, id),
    onSuccess:  () => { invalidate('documents'); flash('Document deleted.') },
    onError:    (e: any) => flash(apiErr(e, 'Failed to delete document.')),
  })

  // ── Save handlers ──────────────────────────────────────────────────────────
  const saveGeneral = () => {
    saveTenantMut.mutate({
      organisation_name: formData.organisation_name || undefined,
      trading_name:      formData.trading_name      || null,
      organisation_type: formData.organisation_type || null,
      primary_email:     formData.primary_email     || undefined,
      primary_phone:     formData.primary_phone     || null,
      website_url:       formData.website_url       || null,
      timezone:          formData.timezone          || undefined,
    })
    if (formData.default_funding_type !== undefined) {
      saveConfigMut.mutate({ default_funding_type: formData.default_funding_type })
    }
  }

  const saveAbn = () => {
    saveTenantMut.mutate({
      abn:                      abnFormData.abn ? abnFormData.abn.replace(/\s/g, '').slice(0, 11) : null,
      acn:                      abnFormData.acn ? abnFormData.acn.replace(/\s/g, '').slice(0, 9) : null,
      ndis_registration_number: abnFormData.ndis_registration_number || null,
      registration_expiry_date: abnFormData.registration_expiry_date || null,
      provider_type:            abnFormData.provider_type            || null,
    })
  }

  const startEdit    = () => { setForm({ ...tenant }); setEditMode(true) }
  const cancelEdit   = () => setEditMode(false)
  const setField     = (key: string, val: string) => setForm((f: any) => ({ ...f, [key]: val }))

  const startAbnEdit  = () => { setAbnForm({ ...tenant }); setAbnEditMode(true) }
  const cancelAbnEdit = () => setAbnEditMode(false)
  const setAbnField   = (key: string, val: string) => setAbnForm((f: any) => ({ ...f, [key]: val }))

  // ── Document upload ────────────────────────────────────────────────────────
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > MAX_FILE_MB * 1024 * 1024) {
      setFileError(`File exceeds ${MAX_FILE_MB} MB limit.`)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }
    setFileError('')
    setUploadFile(file)
    setUploadForm({ name: file.name.replace(/\.[^.]+$/, ''), category: 'Registration', categoryOther: '', linked_to: '', expiry: '' })
    setShowUploadModal(true)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const confirmUpload = () => {
    if (!uploadFile) return
    const category = uploadForm.category === 'Other'
      ? (uploadForm.categoryOther.trim() || 'Other')
      : uploadForm.category
    createDocMut.mutate({
      document_name:     uploadForm.name || uploadFile.name.replace(/\.[^.]+$/, ''),
      document_category: category,
      file_path:         `local:${uploadFile.name}`,
      file_size_kb:      Math.round(uploadFile.size / 1024),
      mime_type:         uploadFile.type || null,
      linked_to:         uploadForm.linked_to || null,
      expiry_date:       uploadForm.expiry || null,
    }, {
      onSuccess: () => {
        setShowUploadModal(false)
        setUploadFile(null)
      },
    })
  }

  // ── Derived ────────────────────────────────────────────────────────────────
  const allDocCategories   = ['All', ...Array.from(new Set(docs.map((d: any) => d.document_category)))]
  const filteredDocs       = docFilter === 'All' ? docs : docs.filter((d: any) => d.document_category === docFilter)
  const ndisExpiry         = expiryStatus(tenant?.registration_expiry_date)

  return (
    <Layout title="Organisation">
      <div className="space-y-4">
        {msg && (
          <div className="text-sm text-purple-700 bg-purple-50 border border-purple-200 px-3 py-2 rounded-lg">
            {msg}
          </div>
        )}

        {/* ── Tab bar ────────────────────────────────────────────────────── */}
        <div className="flex gap-0 border-b border-slate-200 overflow-x-auto">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap ${
                activeTab === id
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}>
              <Icon className="h-4 w-4" />{label}
            </button>
          ))}
        </div>

        {isLoading ? <SkeletonOrgTab /> : (
          <>
            {/* ══════════════════════════════════════════════════════════════ */}
            {/* 2.1 ORGANISATION INFORMATION MANAGEMENT                       */}
            {/* ══════════════════════════════════════════════════════════════ */}
            {activeTab === 'general' && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Organisation Information</CardTitle>
                    <p className="text-xs text-slate-400 mt-0.5">Maintain accurate organisation details used across the system.</p>
                  </div>
                  <div className="flex gap-2">
                    {editMode ? (
                      <>
                        <Button size="sm" onClick={saveGeneral} disabled={saveTenantMut.isPending}>
                          <Save className="h-3 w-3 mr-1" />{saveTenantMut.isPending ? 'Saving…' : 'Save Changes'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={cancelEdit}>
                          <X className="h-3 w-3 mr-1" />Cancel
                        </Button>
                      </>
                    ) : (
                      <Button size="sm" variant="outline" onClick={startEdit}>
                        <Edit2 className="h-3 w-3 mr-1" />Edit
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Legal Identity */}
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3 pb-1 border-b border-slate-100">Legal Identity</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Organisation Legal Name <span className="text-red-400">*</span></label>
                        {editMode
                          ? <Input value={formData.organisation_name || ''} onChange={e => setField('organisation_name', e.target.value)} />
                          : <p className="text-sm text-slate-800 font-medium">{tenant?.organisation_name || '—'}</p>}
                      </div>
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Trading Name</label>
                        {editMode
                          ? <Input value={formData.trading_name || ''} onChange={e => setField('trading_name', e.target.value)} placeholder="If different from legal name" />
                          : <p className="text-sm text-slate-800 font-medium">{tenant?.trading_name || <span className="text-slate-400 font-normal">—</span>}</p>}
                      </div>
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Business / Organisation Type</label>
                        {editMode
                          ? (
                            <select value={formData.organisation_type || ''} onChange={e => setField('organisation_type', e.target.value)} className={selectCls + ' w-full'}>
                              <option value="">— Select —</option>
                              {['Company', 'Non-Profit', 'Sole Trader', 'Partnership', 'Trust', 'Government', 'Association'].map(t => <option key={t}>{t}</option>)}
                            </select>
                          )
                          : <p className="text-sm text-slate-800 font-medium">{tenant?.organisation_type || <span className="text-slate-400 font-normal">—</span>}</p>}
                      </div>
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Status</label>
                        <div>
                          <Badge variant={tenant?.status?.toLowerCase() === 'active' ? 'success' : 'destructive'}>
                            {tenant?.status || 'Active'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Contact & Online Presence */}
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3 pb-1 border-b border-slate-100">Contact &amp; Online Presence</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {[
                        { label: 'Primary Email', key: 'primary_email', type: 'email' },
                        { label: 'Primary Phone', key: 'primary_phone', type: 'tel' },
                        { label: 'Website',       key: 'website_url',   type: 'url' },
                      ].map(({ label, key, type }) => (
                        <div key={key} className="space-y-1.5">
                          <label className={fieldLabel}>{label}</label>
                          {editMode
                            ? <Input type={type} value={formData[key] || ''} onChange={e => setField(key, e.target.value)} />
                            : <p className="text-sm text-slate-800 font-medium">{tenant?.[key] || <span className="text-slate-400 font-normal">—</span>}</p>}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Operational Settings */}
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3 pb-1 border-b border-slate-100">Operational Settings</p>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Timezone</label>
                        {editMode ? (
                          <select value={formData.timezone || 'Australia/Sydney'} onChange={e => setField('timezone', e.target.value)} className={selectCls + ' w-full'}>
                            {Object.entries(TZ_LABELS).map(([tz, label]) => (
                              <option key={tz} value={tz}>{label}</option>
                            ))}
                          </select>
                        ) : (
                          <p className="text-sm text-slate-800 font-medium">
                            {TZ_LABELS[tenant?.timezone || 'Australia/Sydney'] || tenant?.timezone || '—'}
                          </p>
                        )}
                      </div>
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Default Funding Type</label>
                        {editMode ? (
                          <select value={formData.default_funding_type || ''} onChange={e => setField('default_funding_type', e.target.value)} className={selectCls + ' w-full'}>
                            <option value="">— Select —</option>
                            <option value="Agency Managed">Agency Managed</option>
                            <option value="Plan Managed">Plan Managed</option>
                            <option value="Self Managed">Self Managed</option>
                          </select>
                        ) : (
                          <p className="text-sm text-slate-800 font-medium">
                            {tenant?.default_funding_type || <span className="text-slate-400 font-normal">Not set</span>}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ══════════════════════════════════════════════════════════════ */}
            {/* 2.2 ABN & NDIS REGISTRATION MANAGEMENT                        */}
            {/* ══════════════════════════════════════════════════════════════ */}
            {activeTab === 'abn' && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>ABN &amp; NDIS Registration</CardTitle>
                    <p className="text-xs text-slate-400 mt-0.5">Manage registration numbers, status, and expiry dates.</p>
                  </div>
                  <div className="flex gap-2">
                    {abnEditMode ? (
                      <>
                        <Button size="sm" onClick={saveAbn} disabled={saveTenantMut.isPending}>
                          <Save className="h-3 w-3 mr-1" />{saveTenantMut.isPending ? 'Saving…' : 'Save Changes'}
                        </Button>
                        <Button size="sm" variant="outline" onClick={cancelAbnEdit}>
                          <X className="h-3 w-3 mr-1" />Cancel
                        </Button>
                      </>
                    ) : (
                      <Button size="sm" variant="outline" onClick={startAbnEdit}>
                        <Edit2 className="h-3 w-3 mr-1" />Edit
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* ABN Details */}
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3 pb-1 border-b border-slate-100">ABN Details</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Australian Business Number (ABN)</label>
                        {abnEditMode
                          ? <Input value={abnFormData.abn || ''} onChange={e => setAbnField('abn', e.target.value)} placeholder="XX XXX XXX XXX" maxLength={14} />
                          : (
                            <div className="flex items-center gap-2">
                              <p className="text-sm text-slate-800 font-medium font-mono">{tenant?.abn ? tenant.abn.replace(/(\d{2})(\d{3})(\d{3})(\d{3})/, '$1 $2 $3 $4') : '—'}</p>
                              {tenant?.abn && <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium">✓ Registered</span>}
                            </div>
                          )}
                      </div>
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Australian Company Number (ACN)</label>
                        {abnEditMode
                          ? <Input value={abnFormData.acn || ''} onChange={e => setAbnField('acn', e.target.value)} placeholder="XXX XXX XXX" maxLength={11} />
                          : <p className="text-sm text-slate-800 font-medium font-mono">{tenant?.acn || <span className="text-slate-400 font-normal font-sans">—</span>}</p>}
                      </div>
                    </div>
                  </div>

                  {/* NDIS Registration */}
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3 pb-1 border-b border-slate-100">NDIS Registration</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>NDIS Registration Number</label>
                        {abnEditMode
                          ? <Input value={abnFormData.ndis_registration_number || ''} onChange={e => setAbnField('ndis_registration_number', e.target.value)} placeholder="e.g. 4050012345" />
                          : <p className="text-sm text-slate-800 font-medium font-mono">{tenant?.ndis_registration_number || <span className="text-slate-400 font-normal font-sans">—</span>}</p>}
                      </div>
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>NDIS Provider Type</label>
                        {abnEditMode ? (
                          <div className="flex rounded-lg border border-slate-200 bg-white p-1 w-fit">
                            {['Registered', 'Non-Registered'].map(pt => (
                              <button key={pt} type="button"
                                onClick={() => setAbnField('provider_type', pt)}
                                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                                  abnFormData.provider_type === pt
                                    ? 'bg-purple-800 text-white shadow-sm'
                                    : 'text-slate-500 hover:text-slate-700'
                                }`}>
                                {pt}
                              </button>
                            ))}
                          </div>
                        ) : (
                          <div>
                            <Badge variant={tenant?.provider_type === 'Registered' ? 'success' : 'secondary'}>
                              {tenant?.provider_type || 'Not specified'}
                            </Badge>
                          </div>
                        )}
                      </div>
                      <div className="space-y-1.5">
                        <label className={fieldLabel}>Registration Expiry Date</label>
                        {abnEditMode
                          ? (
                            <input type="date" value={abnFormData.registration_expiry_date || ''}
                              onChange={e => setAbnField('registration_expiry_date', e.target.value)}
                              className={selectCls + ' w-full'} />
                          )
                          : (
                            <div className="flex items-center gap-2">
                              <p className="text-sm text-slate-800 font-medium">
                                {tenant?.registration_expiry_date
                                  ? new Date(tenant.registration_expiry_date).toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric' })
                                  : <span className="text-slate-400 font-normal">Not set</span>}
                              </p>
                              {tenant?.registration_expiry_date && (
                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ndisExpiry.bg} ${ndisExpiry.color}`}>
                                  {ndisExpiry.days !== null && ndisExpiry.days < 0
                                    ? 'Expired'
                                    : `${ndisExpiry.label} remaining`}
                                </span>
                              )}
                            </div>
                          )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ══════════════════════════════════════════════════════════════ */}
            {/* 2.3 CONTACT & ADDRESS MANAGEMENT                              */}
            {/* ══════════════════════════════════════════════════════════════ */}
            {activeTab === 'contacts' && (
              <div className="space-y-4">
                {/* Contacts */}
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>Contacts</CardTitle>
                      <p className="text-xs text-slate-400 mt-0.5">Maintain contact persons for operational and administrative processes.</p>
                    </div>
                    <Button size="sm" onClick={() => setShowAddContact(!showAddContact)}>
                      <Plus className="h-4 w-4 mr-1" />Add contact
                    </Button>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {showAddContact && (
                      <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 space-y-3">
                        <h4 className="text-sm font-semibold text-slate-700">New Contact</h4>
                        <div className="grid grid-cols-2 gap-3">
                          <Input placeholder="First name" value={newContact.first_name} onChange={e => setNewContact({ ...newContact, first_name: e.target.value })} />
                          <Input placeholder="Last name"  value={newContact.last_name}  onChange={e => setNewContact({ ...newContact, last_name: e.target.value })} />
                          <Input placeholder="Position title (optional)" value={newContact.position_title} onChange={e => setNewContact({ ...newContact, position_title: e.target.value })} />
                          <select value={newContact.contact_type} onChange={e => setNewContact({ ...newContact, contact_type: e.target.value })} className={selectCls}>
                            {['Primary', 'Secondary', 'Billing', 'Emergency', 'Operations', 'Compliance'].map(t => <option key={t}>{t}</option>)}
                          </select>
                          <Input placeholder="Email" type="email" value={newContact.email} onChange={e => setNewContact({ ...newContact, email: e.target.value })} />
                          <Input placeholder="Phone"             value={newContact.phone} onChange={e => setNewContact({ ...newContact, phone: e.target.value })} />
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => addContactMut.mutate(newContact)} disabled={addContactMut.isPending}>Save</Button>
                          <Button size="sm" variant="outline" onClick={() => setShowAddContact(false)}>Cancel</Button>
                        </div>
                      </div>
                    )}
                    {contacts.length === 0 ? (
                      <p className="text-sm text-slate-400 text-center py-8">No contacts yet. Add your first contact.</p>
                    ) : (
                      <div className="space-y-3">
                        {contacts.map((c: any) => {
                          const cId     = c.contact_id ?? c.id
                          const fullName = [c.first_name, c.last_name].filter(Boolean).join(' ') || c.contact_name || '—'
                          return (
                            <div key={cId} className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                              {editContactId === cId ? (
                                <div className="space-y-3">
                                  <div className="grid grid-cols-2 gap-3">
                                    <Input placeholder="First name"    value={editContactForm.first_name    || ''} onChange={e => setEditContactForm((f: any) => ({ ...f, first_name:    e.target.value }))} />
                                    <Input placeholder="Last name"     value={editContactForm.last_name     || ''} onChange={e => setEditContactForm((f: any) => ({ ...f, last_name:     e.target.value }))} />
                                    <Input placeholder="Position title" value={editContactForm.position_title || ''} onChange={e => setEditContactForm((f: any) => ({ ...f, position_title: e.target.value }))} />
                                    <select value={editContactForm.contact_type || 'Primary'} onChange={e => setEditContactForm((f: any) => ({ ...f, contact_type: e.target.value }))} className={selectCls}>
                                      {['Primary', 'Secondary', 'Billing', 'Emergency', 'Operations', 'Compliance'].map(t => <option key={t}>{t}</option>)}
                                    </select>
                                    <Input placeholder="Email" value={editContactForm.email || ''} onChange={e => setEditContactForm((f: any) => ({ ...f, email: e.target.value }))} />
                                    <Input placeholder="Phone" value={editContactForm.phone || ''} onChange={e => setEditContactForm((f: any) => ({ ...f, phone: e.target.value }))} />
                                  </div>
                                  <div className="flex gap-2">
                                    <Button size="sm" onClick={() => updateContactMut.mutate({ id: cId, data: editContactForm })} disabled={updateContactMut.isPending}>
                                      <Save className="h-3 w-3 mr-1" />Save
                                    </Button>
                                    <Button size="sm" variant="outline" onClick={() => setEditContactId(null)}>Cancel</Button>
                                  </div>
                                </div>
                              ) : (
                                <>
                                  <div className="flex items-start justify-between mb-3">
                                    <div>
                                      <p className="text-sm font-semibold text-slate-800">{fullName}</p>
                                      <p className="text-xs text-slate-400 mt-0.5">{c.position_title || c.contact_type}</p>
                                    </div>
                                    <div className="flex gap-2 items-center">
                                      <Badge variant="secondary">{c.contact_type}</Badge>
                                      <button onClick={() => { setEditContactId(cId); setEditContactForm({ ...c }) }}
                                        className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-purple-600 hover:border-purple-300">
                                        <Edit2 className="h-3 w-3" />
                                      </button>
                                    </div>
                                  </div>
                                  <div className="grid grid-cols-3 gap-3">
                                    {c.email  && <div><label className={fieldLabel}>Email</label> <p className="text-xs text-slate-700 mt-0.5">{c.email}</p></div>}
                                    {c.phone  && <div><label className={fieldLabel}>Phone</label> <p className="text-xs text-slate-700 mt-0.5">{c.phone}</p></div>}
                                    {c.mobile && <div><label className={fieldLabel}>Mobile</label><p className="text-xs text-slate-700 mt-0.5">{c.mobile}</p></div>}
                                  </div>
                                </>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Addresses */}
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>Addresses</CardTitle>
                      <p className="text-xs text-slate-400 mt-0.5">Multiple addresses supported for registered, postal, and operational locations.</p>
                    </div>
                    <Button size="sm" onClick={() => setShowAddAddress(!showAddAddress)}>
                      <Plus className="h-4 w-4 mr-1" />Add address
                    </Button>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {showAddAddress && (
                      <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 space-y-3">
                        <h4 className="text-sm font-semibold text-slate-700">New Address</h4>
                        <div className="grid grid-cols-2 gap-3">
                          <select value={newAddress.address_type} onChange={e => setNewAddress({ ...newAddress, address_type: e.target.value })} className={selectCls}>
                            {['Business', 'Postal', 'Branch', 'Registered', 'Head Office'].map(t => <option key={t}>{t}</option>)}
                          </select>
                          <Input placeholder="Street address" value={newAddress.address_line1} onChange={e => setNewAddress({ ...newAddress, address_line1: e.target.value })} />
                          <Input placeholder="Suburb"         value={newAddress.suburb}        onChange={e => setNewAddress({ ...newAddress, suburb: e.target.value })} />
                          <select value={newAddress.state_code} onChange={e => setNewAddress({ ...newAddress, state_code: e.target.value })} className={selectCls}>
                            {STATES.map(s => <option key={s}>{s}</option>)}
                          </select>
                          <Input placeholder="Postcode" value={newAddress.postcode} onChange={e => setNewAddress({ ...newAddress, postcode: e.target.value })} maxLength={4} />
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" onClick={() => addAddressMut.mutate(newAddress)} disabled={addAddressMut.isPending}>Save</Button>
                          <Button size="sm" variant="outline" onClick={() => setShowAddAddress(false)}>Cancel</Button>
                        </div>
                      </div>
                    )}
                    {addresses.length === 0 ? (
                      <p className="text-sm text-slate-400 text-center py-8">No addresses yet. Add your first address.</p>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {addresses.map((a: any) => {
                          const aId = a.address_id ?? a.id
                          return (
                            <div key={aId} className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                              {editAddressId === aId ? (
                                <div className="space-y-3">
                                  <div className="grid grid-cols-2 gap-3">
                                    <select value={editAddressForm.address_type || 'Business'} onChange={e => setEditAddressForm((f: any) => ({ ...f, address_type: e.target.value }))} className={selectCls}>
                                      {['Business', 'Postal', 'Branch', 'Registered', 'Head Office'].map(t => <option key={t}>{t}</option>)}
                                    </select>
                                    <Input placeholder="Street address" value={editAddressForm.address_line1 || ''} onChange={e => setEditAddressForm((f: any) => ({ ...f, address_line1: e.target.value }))} />
                                    <Input placeholder="Suburb"         value={editAddressForm.suburb        || ''} onChange={e => setEditAddressForm((f: any) => ({ ...f, suburb:        e.target.value }))} />
                                    <select value={editAddressForm.state_code || 'NSW'} onChange={e => setEditAddressForm((f: any) => ({ ...f, state_code: e.target.value }))} className={selectCls}>
                                      {STATES.map(s => <option key={s}>{s}</option>)}
                                    </select>
                                    <Input placeholder="Postcode" value={editAddressForm.postcode || ''} onChange={e => setEditAddressForm((f: any) => ({ ...f, postcode: e.target.value }))} maxLength={4} />
                                  </div>
                                  <div className="flex gap-2">
                                    <Button size="sm" onClick={() => updateAddressMut.mutate({ id: aId, data: editAddressForm })} disabled={updateAddressMut.isPending}>
                                      <Save className="h-3 w-3 mr-1" />Save
                                    </Button>
                                    <Button size="sm" variant="outline" onClick={() => setEditAddressId(null)}>Cancel</Button>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex items-start justify-between">
                                  <div>
                                    <Badge variant="secondary" className="mb-2">{a.address_type}</Badge>
                                    <p className="text-sm font-medium text-slate-800 mt-1">{a.address_line1}</p>
                                    {a.address_line2 && <p className="text-xs text-slate-600">{a.address_line2}</p>}
                                    <p className="text-xs text-slate-600">{[a.suburb, a.state_code, a.postcode].filter(Boolean).join(' ')}</p>
                                    {a.country_code && a.country_code !== 'AUS' && <p className="text-xs text-slate-400">{a.country_code}</p>}
                                  </div>
                                  <button onClick={() => { setEditAddressId(aId); setEditAddressForm({ ...a }) }}
                                    className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-purple-600 hover:border-purple-300">
                                    <Edit2 className="h-3 w-3" />
                                  </button>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {/* ══════════════════════════════════════════════════════════════ */}
            {/* 2.4 REGISTRATION EXPIRY TRACKING                              */}
            {/* ══════════════════════════════════════════════════════════════ */}
            {activeTab === 'expiry' && (
              <div className="space-y-4">
                {/* Alert banners */}
                {ndisExpiry.days !== null && ndisExpiry.days < 0 && (
                  <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                    <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-semibold text-red-700">NDIS Registration has expired</p>
                      <p className="text-xs text-red-600 mt-0.5">
                        Expired on {new Date(tenant.registration_expiry_date!).toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric' })}. Immediate renewal required.
                      </p>
                    </div>
                  </div>
                )}
                {ndisExpiry.days !== null && ndisExpiry.days >= 0 && ndisExpiry.days <= 90 && (
                  <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
                    <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-semibold text-amber-700">NDIS Registration expiring soon</p>
                      <p className="text-xs text-amber-600 mt-0.5">
                        Expires in {ndisExpiry.days} days on {new Date(tenant.registration_expiry_date!).toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric' })}. Please arrange renewal.
                      </p>
                    </div>
                  </div>
                )}

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>Registration Expiry Tracking</CardTitle>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Track expiry dates to prevent compliance lapses. Update dates in the <button onClick={() => setActiveTab('abn')} className="text-purple-600 underline underline-offset-2">ABN &amp; NDIS</button> tab.
                      </p>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* NDIS Registration Expiry card */}
                    <div className={`rounded-xl border-2 p-5 ${
                      !tenant?.registration_expiry_date ? 'border-slate-200 bg-slate-50'
                      : ndisExpiry.days !== null && ndisExpiry.days < 0   ? 'border-red-200 bg-red-50'
                      : ndisExpiry.days !== null && ndisExpiry.days <= 90  ? 'border-amber-200 bg-amber-50'
                      : 'border-emerald-200 bg-emerald-50'
                    }`}>
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <p className="text-sm font-bold text-slate-800">NDIS Provider Registration</p>
                          <p className="text-xs text-slate-500">Reg# {tenant?.ndis_registration_number || '—'}</p>
                        </div>
                        <div className="text-right">
                          {!tenant?.registration_expiry_date ? (
                            <span className="text-xs px-3 py-1 rounded-full bg-slate-200 text-slate-600 font-medium">Not set</span>
                          ) : ndisExpiry.days !== null && ndisExpiry.days < 0 ? (
                            <div className="flex items-center gap-1.5">
                              <XCircle className="h-4 w-4 text-red-500" />
                              <span className="text-xs px-3 py-1 rounded-full bg-red-100 text-red-700 font-bold">Expired</span>
                            </div>
                          ) : ndisExpiry.days !== null && ndisExpiry.days <= 90 ? (
                            <div className="flex items-center gap-1.5">
                              <AlertTriangle className="h-4 w-4 text-amber-500" />
                              <span className="text-xs px-3 py-1 rounded-full bg-amber-100 text-amber-700 font-bold">Expiring</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1.5">
                              <CheckCircle className="h-4 w-4 text-emerald-500" />
                              <span className="text-xs px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 font-bold">Valid</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {tenant?.registration_expiry_date && (
                        <div className="mt-4 space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className={`text-2xl font-extrabold ${ndisExpiry.color}`}>
                              {ndisExpiry.days !== null && ndisExpiry.days < 0
                                ? `${Math.abs(ndisExpiry.days)} days ago`
                                : `${ndisExpiry.days} days remaining`}
                            </span>
                            <span className="text-slate-500">
                              Expires: {new Date(tenant.registration_expiry_date).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })}
                            </span>
                          </div>
                          {/* Progress bar */}
                          <div className="w-full bg-slate-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all ${
                                ndisExpiry.days !== null && ndisExpiry.days < 0   ? 'w-full bg-red-500'
                                : ndisExpiry.days !== null && ndisExpiry.days <= 90 ? 'bg-amber-400'
                                : 'bg-emerald-500'
                              }`}
                              style={{
                                width: ndisExpiry.days !== null && ndisExpiry.days >= 0
                                  ? `${Math.min(100, Math.max(5, (ndisExpiry.days / 365) * 100))}%`
                                  : '100%'
                              }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="mt-4 flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => setActiveTab('abn')}>
                          <Edit2 className="h-3 w-3 mr-1" />Update Expiry Date
                        </Button>
                        {docs.filter((d: any) => d.linked_to === 'NDIS Registration').length > 0 && (
                          <Button size="sm" variant="outline" onClick={() => setActiveTab('documents')}>
                            <FileText className="h-3 w-3 mr-1" />View Documents
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Document expiry summary */}
                    {docs.filter((d: any) => d.expiry_date).length > 0 && (
                      <div className="mt-6">
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Document Expiries</p>
                        <div className="space-y-2">
                          {docs
                            .filter((d: any) => d.expiry_date)
                            .sort((a: any, b: any) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime())
                            .map((d: any) => {
                              const st   = docExpiryStatus(d.expiry_date)
                              const days = Math.round((new Date(d.expiry_date).getTime() - Date.now()) / 86400000)
                              return (
                                <div key={d.document_id} className="flex items-center justify-between bg-white border border-slate-200 rounded-lg px-4 py-2.5">
                                  <div>
                                    <p className="text-sm font-medium text-slate-800">{d.document_name}</p>
                                    <p className="text-xs text-slate-400">{d.document_category}{d.linked_to ? ` · ${d.linked_to}` : ''}</p>
                                  </div>
                                  <div className="flex items-center gap-3 text-right">
                                    <p className="text-xs text-slate-500">
                                      {new Date(d.expiry_date).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })}
                                    </p>
                                    <StatusPill status={st} />
                                  </div>
                                </div>
                              )
                            })}
                        </div>
                      </div>
                    )}

                    {!tenant?.registration_expiry_date && docs.filter((d: any) => d.expiry_date).length === 0 && (
                      <div className="text-center py-10 mt-4 border border-dashed border-slate-200 rounded-xl">
                        <Clock className="h-8 w-8 text-slate-300 mx-auto mb-3" />
                        <p className="text-sm font-medium text-slate-500">No expiry dates tracked yet</p>
                        <p className="text-xs text-slate-400 mt-1">
                          Set a registration expiry date in the ABN &amp; NDIS tab, or upload documents with expiry dates.
                        </p>
                        <Button size="sm" className="mt-4" variant="outline" onClick={() => setActiveTab('abn')}>
                          Go to ABN &amp; NDIS Tab
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {/* ══════════════════════════════════════════════════════════════ */}
            {/* 2.5 ORGANISATION DOCUMENT MANAGEMENT                          */}
            {/* ══════════════════════════════════════════════════════════════ */}
            {activeTab === 'documents' && (
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Organisation Documents</CardTitle>
                    <p className="text-xs text-slate-400 mt-0.5">Upload and manage registration certificates, insurance policies, and compliance documents.</p>
                  </div>
                  <div>
                    <input ref={fileInputRef} type="file" accept={ACCEPTED} className="hidden" onChange={handleFileChange} />
                    <Button size="sm" onClick={() => fileInputRef.current?.click()}>
                      <Upload className="h-4 w-4 mr-1" />Upload Document
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-xs text-slate-400">
                    Accepted: PDF, DOCX, PNG, JPG · Max size: <span className="font-medium text-slate-600">5 MB</span> · Access restricted to Admin users.
                  </p>
                  {fileError && (
                    <p className="text-xs text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg">{fileError}</p>
                  )}

                  {/* Category filter chips */}
                  <div className="flex gap-2 flex-wrap">
                    {allDocCategories.map(cat => (
                      <button key={cat} onClick={() => setDocFilter(cat)}
                        className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
                          docFilter === cat
                            ? 'bg-purple-800 text-white border-purple-800'
                            : 'bg-white text-slate-500 border-slate-200 hover:border-purple-300 hover:text-purple-600'
                        }`}>
                        {cat}
                      </button>
                    ))}
                  </div>

                  {/* Documents table */}
                  {filteredDocs.length === 0 ? (
                    <div className="text-center py-12">
                      <File className="h-8 w-8 text-slate-300 mx-auto mb-3" />
                      <p className="text-sm text-slate-400">No documents in this category.</p>
                      <p className="text-xs text-slate-400 mt-1">Click "Upload Document" to add one.</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-100">
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wide pb-2 pr-4">Document</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wide pb-2 pr-4">Category</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wide pb-2 pr-4">Linked To</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wide pb-2 pr-4">Uploaded</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wide pb-2 pr-4">Expiry</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wide pb-2 pr-4">Status</th>
                            <th className="pb-2" />
                          </tr>
                        </thead>
                        <tbody>
                          {filteredDocs.map((doc: any) => {
                            const ext = doc.file_path?.split('.').pop()?.toUpperCase()?.slice(0, 4) || 'FILE'
                            const sizeMB = doc.file_size_kb ? `${(doc.file_size_kb / 1024).toFixed(1)} MB` : null
                            const status = docExpiryStatus(doc.expiry_date)
                            return (
                              <tr key={doc.document_id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50">
                                <td className="py-3 pr-4">
                                  <div className="flex items-center gap-2">
                                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${ext === 'PDF' ? 'bg-red-100 text-red-600' : 'bg-purple-100 text-purple-600'}`}>{ext}</span>
                                    <div>
                                      <p className="font-medium text-slate-800 text-xs">{doc.document_name}</p>
                                      {sizeMB && <p className="text-xs text-slate-400">{sizeMB}</p>}
                                    </div>
                                  </div>
                                </td>
                                <td className="py-3 pr-4">
                                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                                    {doc.document_category}
                                  </span>
                                </td>
                                <td className="py-3 pr-4 text-xs text-slate-500">{doc.linked_to || <span className="text-slate-300">—</span>}</td>
                                <td className="py-3 pr-4 text-xs text-slate-600">
                                  {new Date(doc.uploaded_at).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })}
                                </td>
                                <td className="py-3 pr-4 text-xs text-slate-600">
                                  {doc.expiry_date
                                    ? new Date(doc.expiry_date).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })
                                    : <span className="text-slate-400">No expiry</span>}
                                </td>
                                <td className="py-3 pr-4"><StatusPill status={status} /></td>
                                <td className="py-3">
                                  <div className="flex gap-1.5">
                                    <button className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:text-slate-700" title="Download">
                                      <Download className="h-3.5 w-3.5" />
                                    </button>
                                    <button
                                      onClick={() => { if (window.confirm('Delete this document?')) deleteDocMut.mutate(doc.document_id) }}
                                      className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:text-red-500 hover:border-red-300"
                                      title="Delete"
                                      disabled={deleteDocMut.isPending}>
                                      <Trash2 className="h-3.5 w-3.5" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

          </>
        )}
      </div>

      {/* ── Upload Document Modal ──────────────────────────────────────────── */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <div>
                <h2 className="text-base font-semibold text-slate-900">Upload Document</h2>
                <p className="text-xs text-slate-400 mt-0.5">Max file size: 5 MB · PDF, DOCX, PNG, JPG</p>
              </div>
              <button onClick={() => { setShowUploadModal(false); setUploadFile(null) }}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* File preview */}
            <div className="mx-6 mt-5 flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3">
              <span className={`text-xs font-bold px-2 py-1 rounded ${
                uploadFile?.name.toLowerCase().endsWith('.pdf') ? 'bg-red-100 text-red-600' : 'bg-purple-100 text-purple-600'
              }`}>
                {uploadFile?.name.split('.').pop()?.toUpperCase()}
              </span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-800 truncate">{uploadFile?.name}</p>
                <p className="text-xs text-slate-400">{uploadFile ? (uploadFile.size / (1024 * 1024)).toFixed(2) + ' MB' : ''}</p>
              </div>
            </div>

            {/* Form fields */}
            <div className="px-6 py-4 space-y-4">
              <div className="space-y-1.5">
                <label className={fieldLabel}>Document Name <span className="text-red-400">*</span></label>
                <Input value={uploadForm.name} onChange={e => setUploadForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g. NDIS Registration Certificate 2025" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className={fieldLabel}>Category</label>
                  <select value={uploadForm.category} onChange={e => setUploadForm(f => ({ ...f, category: e.target.value, categoryOther: '' }))} className={selectCls + ' w-full'}>
                    {DOC_CATEGORIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                  {uploadForm.category === 'Other' && (
                    <Input value={uploadForm.categoryOther} onChange={e => setUploadForm(f => ({ ...f, categoryOther: e.target.value }))}
                      placeholder="Category name" className="mt-2" autoFocus />
                  )}
                </div>
                <div className="space-y-1.5">
                  <label className={fieldLabel}>Linked To</label>
                  <select value={uploadForm.linked_to} onChange={e => setUploadForm(f => ({ ...f, linked_to: e.target.value }))} className={selectCls + ' w-full'}>
                    {DOC_LINKED_OPTIONS.map(o => <option key={o} value={o}>{o || '— Not linked —'}</option>)}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className={fieldLabel}>Expiry Date <span className="text-slate-400 font-normal normal-case tracking-normal">(optional)</span></label>
                <input type="date" value={uploadForm.expiry} onChange={e => setUploadForm(f => ({ ...f, expiry: e.target.value }))}
                  className={selectCls + ' w-full'} />
              </div>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 pb-5">
              <Button className="flex-1" onClick={confirmUpload} disabled={!uploadForm.name.trim() || createDocMut.isPending}>
                <Upload className="h-4 w-4 mr-1.5" />
                {createDocMut.isPending ? 'Uploading…' : 'Upload Document'}
              </Button>
              <Button variant="outline" onClick={() => { setShowUploadModal(false); setUploadFile(null) }}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
