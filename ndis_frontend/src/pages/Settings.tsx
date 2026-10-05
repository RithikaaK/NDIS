import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { useAuth } from '@/context/AuthContext'
import { usePermissions } from '@/hooks/usePermissions'
import { getConfig, updateConfig, getTenant, updateTenant } from '@/api/tenant'
import {
  Settings2, Globe, DollarSign, FileText, Bell,
  Lock, Plug, ExternalLink, Save, Info, CheckCircle2,
} from 'lucide-react'

// ── Shared helpers ─────────────────────────────────────────────────────────────
const inputCls  = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent focus:bg-white transition-all"
const selectCls = "w-full h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white transition-all"
const labelCls  = "text-xs font-semibold text-slate-600 uppercase tracking-wide"
const sectionHd = "text-[10px] font-bold text-slate-400 uppercase tracking-widest pb-2 border-b border-slate-100 mb-4"

function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div className="space-y-1.5">
      <label className={labelCls}>{label}</label>
      {children}
      {hint && <p className="text-[11px] text-slate-400">{hint}</p>}
    </div>
  )
}

function Toggle({ checked, onChange, label, desc }: { checked: boolean; onChange: (v: boolean) => void; label: string; desc?: string }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer select-none">
      <div className="relative mt-0.5 flex-shrink-0" onClick={() => onChange(!checked)}>
        <div className={`w-9 h-5 rounded-full transition-colors ${checked ? 'bg-purple-700' : 'bg-slate-200'}`} />
        <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${checked ? 'translate-x-4' : ''}`} />
      </div>
      <div>
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {desc && <p className="text-[11px] text-slate-400">{desc}</p>}
      </div>
    </label>
  )
}

function SaveBar({ dirty, saving, onSave, onReset }: { dirty: boolean; saving: boolean; onSave: () => void; onReset: () => void }) {
  if (!dirty) return null
  return (
    <div className="sticky bottom-0 bg-white border-t border-slate-200 px-5 py-3 flex items-center justify-between shadow-sm z-10">
      <p className="text-sm text-slate-500">You have unsaved changes.</p>
      <div className="flex items-center gap-3">
        <button onClick={onReset} className="h-8 px-4 text-sm text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
          Discard
        </button>
        <button onClick={onSave} disabled={saving}
          className="h-8 px-5 bg-purple-800 hover:bg-purple-900 disabled:opacity-50 text-white text-sm font-semibold rounded-lg flex items-center gap-1.5 transition-colors">
          <Save className="h-3.5 w-3.5" />
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </div>
  )
}

// ── Tab ids ────────────────────────────────────────────────────────────────────
type TabId = 'general' | 'regional' | 'currency' | 'billing' | 'notifications' | 'security' | 'integrations'

const TABS: { id: TabId; label: string; Icon: React.ElementType }[] = [
  { id: 'general',       label: 'General',         Icon: Settings2  },
  { id: 'regional',      label: 'Regional',         Icon: Globe      },
  { id: 'currency',      label: 'Currency & Tax',   Icon: DollarSign },
  { id: 'billing',       label: 'Billing',          Icon: FileText   },
  { id: 'notifications', label: 'Notifications',    Icon: Bell       },
  { id: 'security',      label: 'Security',         Icon: Lock       },
  { id: 'integrations',  label: 'Integrations',     Icon: Plug       },
]

// ── Main ──────────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { user } = useAuth()
  const tenantId  = user?.tenant_id
  const qc        = useQueryClient()
  const navigate  = useNavigate()
  const { can }   = usePermissions()

  const [tab, setTab]     = useState<TabId>('general')
  const [toast, setToast] = useState('')
  const [cfg,   setCfg]   = useState<Record<string, any>>({})
  const [org,   setOrg]   = useState<Record<string, any>>({})
  const [origCfg, setOrigCfg] = useState<Record<string, any>>({})
  const [origOrg, setOrigOrg] = useState<Record<string, any>>({})

  const flash = (m: string) => { setToast(m); setTimeout(() => setToast(''), 3500) }

  // ── Queries ────────────────────────────────────────────────────────────────
  const { data: configData, isLoading: cfgLoading } = useQuery({
    queryKey: ['config', tenantId],
    queryFn:  () => getConfig(tenantId).then((r: any) => r.data),
    enabled:  !!tenantId,
  })
  const { data: tenantData, isLoading: orgLoading } = useQuery({
    queryKey: ['tenant', tenantId],
    queryFn:  () => getTenant(tenantId).then((r: any) => r.data),
    enabled:  !!tenantId,
  })

  useEffect(() => {
    if (configData) { setCfg({ ...configData }); setOrigCfg({ ...configData }) }
  }, [configData])
  useEffect(() => {
    if (tenantData) { setOrg({ ...tenantData }); setOrigOrg({ ...tenantData }) }
  }, [tenantData])

  // ── Mutations ──────────────────────────────────────────────────────────────
  const cfgMut = useMutation({
    mutationFn: (data: any) => updateConfig(tenantId, data),
    onSuccess: (res: any) => {
      const updated = res.data
      setCfg({ ...updated }); setOrigCfg({ ...updated })
      qc.invalidateQueries({ queryKey: ['config', tenantId] })
      flash('Settings saved successfully.')
    },
    onError: () => flash('Failed to save settings.'),
  })
  const orgMut = useMutation({
    mutationFn: (data: any) => updateTenant(tenantId, data),
    onSuccess: (res: any) => {
      const updated = res.data
      setOrg({ ...updated }); setOrigOrg({ ...updated })
      qc.invalidateQueries({ queryKey: ['tenant', tenantId] })
    },
    onError: () => {},
  })

  // ── Change helpers ─────────────────────────────────────────────────────────
  const setC = (key: string, val: any) => setCfg(p => ({ ...p, [key]: val }))
  const setO = (key: string, val: any) => setOrg(p => ({ ...p, [key]: val }))

  const cfgDirty = JSON.stringify(cfg) !== JSON.stringify(origCfg)
  const orgDirty = JSON.stringify(org) !== JSON.stringify(origOrg)
  const dirty    = cfgDirty || orgDirty

  const handleSave = async () => {
    // Build diffs
    const cfgDiff: Record<string, any> = {}
    for (const k in cfg) if (cfg[k] !== origCfg[k]) cfgDiff[k] = cfg[k]
    const orgDiff: Record<string, any> = {}
    for (const k in org) if (org[k] !== origOrg[k]) orgDiff[k] = org[k]

    const promises: Promise<any>[] = []
    if (Object.keys(cfgDiff).length) promises.push(cfgMut.mutateAsync(cfgDiff))
    if (Object.keys(orgDiff).length) promises.push(orgMut.mutateAsync(orgDiff))
    await Promise.all(promises)
  }
  const handleReset = () => { setCfg({ ...origCfg }); setOrg({ ...origOrg }) }

  const saving = cfgMut.isPending || orgMut.isPending
  const loading = cfgLoading || orgLoading

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <Layout title="Settings">
      {toast && (
        <div className="fixed top-5 right-5 z-50 bg-slate-900 text-white text-sm px-4 py-3 rounded-xl shadow-xl flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />{toast}
        </div>
      )}

      <div className="space-y-5 animate-fade-in">

        {/* Header */}
        <div>
          <h1 className="text-xl font-bold text-slate-900">Tenant Configuration</h1>
          <p className="text-sm text-slate-400 mt-0.5">Manage organisation-level preferences, security, and integrations</p>
        </div>

        {/* Tab bar */}
        <div className="border-b border-slate-200 overflow-x-auto">
          <div className="flex min-w-max">
            {TABS.map(({ id, label, Icon }) => (
              <button key={id} onClick={() => setTab(id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
                  tab === id ? 'border-purple-700 text-purple-700' : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}>
                <Icon className="h-3.5 w-3.5" />{label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="border border-slate-200 rounded-xl p-12 text-center text-slate-400 text-sm">Loading configuration…</div>
        ) : (
          <div className="border border-slate-200 rounded-xl bg-white overflow-hidden">

            {/* ── 8.1 General ──────────────────────────────────────────────── */}
            {tab === 'general' && (
              <div className="p-6 space-y-6">
                <p className={sectionHd}>Organisation Preferences</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="Organisation Name">
                    <input className={inputCls} value={org.organisation_name || ''} onChange={e => setO('organisation_name', e.target.value)} />
                  </Field>
                  <Field label="Trading Name">
                    <input className={inputCls} value={org.trading_name || ''} onChange={e => setO('trading_name', e.target.value)} placeholder="If different from legal name" />
                  </Field>
                  <Field label="ABN">
                    <input className={inputCls} value={org.abn || ''} onChange={e => setO('abn', e.target.value)} placeholder="11 digits" />
                  </Field>
                  <Field label="ACN">
                    <input className={inputCls} value={org.acn || ''} onChange={e => setO('acn', e.target.value)} placeholder="9 digits" />
                  </Field>
                  <Field label="Primary Email">
                    <input className={inputCls} type="email" value={org.primary_email || ''} onChange={e => setO('primary_email', e.target.value)} />
                  </Field>
                  <Field label="Primary Phone">
                    <input className={inputCls} value={org.primary_phone || ''} onChange={e => setO('primary_phone', e.target.value)} />
                  </Field>
                  <Field label="Website">
                    <input className={inputCls} value={org.website_url || ''} onChange={e => setO('website_url', e.target.value)} placeholder="https://" />
                  </Field>
                </div>

                <p className={sectionHd}>NDIS Provider Settings</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="NDIS Registration Number">
                    <input className={inputCls} value={org.ndis_registration_number || ''} onChange={e => setO('ndis_registration_number', e.target.value)} placeholder="4300XXXXXX" />
                  </Field>
                  <Field label="Provider Type">
                    <select className={selectCls} value={org.provider_type || ''} onChange={e => setO('provider_type', e.target.value)}>
                      <option value="">Select…</option>
                      {['Registered Provider','Unregistered Provider','Plan Manager','Support Coordinator','ECEI Provider'].map(t => <option key={t}>{t}</option>)}
                    </select>
                  </Field>
                  <Field label="Default Funding Type">
                    <select className={selectCls} value={cfg.default_funding_type || 'Agency Managed'} onChange={e => setC('default_funding_type', e.target.value)}>
                      {['Agency Managed','Plan Managed','Self Managed'].map(t => <option key={t}>{t}</option>)}
                    </select>
                  </Field>
                  <Field label="Organisation Type">
                    <select className={selectCls} value={org.organisation_type || ''} onChange={e => setO('organisation_type', e.target.value)}>
                      <option value="">Select…</option>
                      {['Private Company','Non-Profit','Government Agency','Sole Trader','Partnership','Trust'].map(t => <option key={t}>{t}</option>)}
                    </select>
                  </Field>
                </div>

                <p className={sectionHd}>Operational Flags</p>
                <div className="space-y-3">
                  <Toggle checked={!!cfg.enable_schads_award}
                    onChange={v => setC('enable_schads_award', v)}
                    label="Apply SCHADS Award rates"
                    desc="Use Social, Community, Home Care and Disability Services Award pricing" />
                </div>
              </div>
            )}

            {/* ── 8.2 Regional & Timezone ───────────────────────────────────── */}
            {tab === 'regional' && (
              <div className="p-6 space-y-6">
                <p className={sectionHd}>Location</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="Country">
                    <select className={selectCls} value={cfg.country || 'Australia'} onChange={e => setC('country', e.target.value)}>
                      {['Australia','New Zealand','United Kingdom','United States','Canada'].map(c => <option key={c}>{c}</option>)}
                    </select>
                  </Field>
                  <Field label="State / Territory">
                    <select className={selectCls} value={cfg.state || ''} onChange={e => setC('state', e.target.value)}>
                      <option value="">All states</option>
                      {['NSW','VIC','QLD','SA','WA','TAS','ACT','NT'].map(s => <option key={s}>{s}</option>)}
                    </select>
                  </Field>
                </div>

                <p className={sectionHd}>Timezone</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="System Timezone" hint="Applies to schedules, audit logs, notifications, and all timestamps">
                    <select className={selectCls} value={cfg.timezone || 'Australia/Sydney'} onChange={e => setC('timezone', e.target.value)}>
                      {[
                        'Australia/Sydney','Australia/Melbourne','Australia/Brisbane',
                        'Australia/Perth','Australia/Adelaide','Australia/Hobart',
                        'Australia/Darwin','Pacific/Auckland','UTC',
                      ].map(tz => <option key={tz}>{tz}</option>)}
                    </select>
                  </Field>
                </div>

                <p className={sectionHd}>Date & Time Formats</p>
                <div className="grid grid-cols-3 gap-5">
                  <Field label="Date Format">
                    <select className={selectCls} value={cfg.date_format || 'DD/MM/YYYY'} onChange={e => setC('date_format', e.target.value)}>
                      {['DD/MM/YYYY','MM/DD/YYYY','YYYY-MM-DD','D MMM YYYY'].map(f => <option key={f}>{f}</option>)}
                    </select>
                  </Field>
                  <Field label="Time Format">
                    <select className={selectCls} value={cfg.time_format || '24h'} onChange={e => setC('time_format', e.target.value)}>
                      <option value="24h">24-hour (e.g. 14:30)</option>
                      <option value="12h">12-hour (e.g. 2:30 PM)</option>
                    </select>
                  </Field>
                  <Field label="Week Starts On">
                    <select className={selectCls} value={cfg.week_starts_on || 'Monday'} onChange={e => setC('week_starts_on', e.target.value)}>
                      {['Monday','Sunday','Saturday'].map(d => <option key={d}>{d}</option>)}
                    </select>
                  </Field>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2 text-sm text-blue-800">
                  <Info className="h-4 w-4 flex-shrink-0 mt-0.5 text-blue-600" />
                  The selected timezone is applied consistently across schedules, service delivery records, audit logs, and all time-sensitive activities.
                </div>
              </div>
            )}

            {/* ── 8.3 Currency & Tax ────────────────────────────────────────── */}
            {tab === 'currency' && (
              <div className="p-6 space-y-6">
                <p className={sectionHd}>Currency</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="Default Currency">
                    <select className={selectCls} value={cfg.currency_code || 'AUD'} onChange={e => setC('currency_code', e.target.value)}>
                      {['AUD','NZD','USD','GBP','EUR'].map(c => <option key={c}>{c}</option>)}
                    </select>
                  </Field>
                </div>

                <p className={sectionHd}>GST & Tax Settings</p>
                <div className="space-y-4">
                  <Toggle checked={!!cfg.enable_gst}
                    onChange={v => setC('enable_gst', v)}
                    label="GST Registered"
                    desc="Organisation is registered for Goods and Services Tax (ABN required)" />

                  {cfg.enable_gst && (
                    <div className="grid grid-cols-2 gap-5 ml-12 mt-2">
                      <Field label="GST Rate (%)" hint="Standard NDIS rate is 10%">
                        <input className={inputCls} type="number" min={0} max={30} value={cfg.gst_rate ?? 10} onChange={e => setC('gst_rate', parseInt(e.target.value))} />
                      </Field>
                    </div>
                  )}
                </div>

                <p className={sectionHd}>NDIS Pricing</p>
                <div className="space-y-3">
                  <Toggle checked={!!cfg.enable_schads_award}
                    onChange={v => setC('enable_schads_award', v)}
                    label="Apply SCHADS Award pricing"
                    desc="Automatically apply SCHADS loading rates where applicable" />
                  <Toggle checked={!!cfg.enable_pace_integration}
                    onChange={v => setC('enable_pace_integration', v)}
                    label="Use PACE pricing catalogue"
                    desc="Validate support item prices against the current NDIS PACE price guide" />
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2 text-sm text-amber-800">
                  <Info className="h-4 w-4 flex-shrink-0 mt-0.5 text-amber-600" />
                  GST calculations are applied to invoices and billing based on applicable NDIS pricing rules. Consult your accountant to confirm the correct GST treatment for your service types.
                </div>
              </div>
            )}

            {/* ── 8.4 Billing & Invoice ─────────────────────────────────────── */}
            {tab === 'billing' && (
              <div className="p-6 space-y-6">
                <p className={sectionHd}>Invoice Numbering</p>
                <div className="grid grid-cols-3 gap-5">
                  <Field label="Invoice Prefix" hint="e.g. INV → INV-0001">
                    <input className={inputCls} value={cfg.invoice_prefix || 'INV'} onChange={e => setC('invoice_prefix', e.target.value)} maxLength={10} />
                  </Field>
                  <Field label="Invoice Due (days)" hint="Days after issue before invoice is overdue">
                    <input className={inputCls} type="number" min={1} max={365} value={cfg.invoice_due_days ?? 14} onChange={e => setC('invoice_due_days', parseInt(e.target.value))} />
                  </Field>
                </div>

                <p className={sectionHd}>Billing Preferences</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="Billing Frequency">
                    <select className={selectCls} value={cfg.billing_frequency || 'Monthly'} onChange={e => setC('billing_frequency', e.target.value)}>
                      {['Weekly','Fortnightly','Monthly','Quarterly','Per Service'].map(f => <option key={f}>{f}</option>)}
                    </select>
                  </Field>
                  <Field label="Payment Terms">
                    <input className={inputCls} value={cfg.payment_terms || ''} onChange={e => setC('payment_terms', e.target.value)} placeholder="e.g. Net 14, EFT only" />
                  </Field>
                </div>

                <p className={sectionHd}>Automation</p>
                <div className="space-y-3">
                  <Toggle checked={!!cfg.auto_invoice_enabled}
                    onChange={v => setC('auto_invoice_enabled', v)}
                    label="Automatic Invoice Generation"
                    desc="Automatically generate invoices at the end of each billing period" />
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2 text-sm text-blue-800">
                  <Info className="h-4 w-4 flex-shrink-0 mt-0.5 text-blue-600" />
                  These settings are applied when invoices are generated, processed, exported, or sent to participants and payers.
                </div>
              </div>
            )}

            {/* ── 8.5 Notifications ─────────────────────────────────────────── */}
            {tab === 'notifications' && (
              <div className="p-6 space-y-6">
                <p className={sectionHd}>Notification Channels</p>
                <div className="space-y-3">
                  <Toggle checked={!!cfg.notify_email_enabled}    onChange={v => setC('notify_email_enabled', v)}    label="Email Notifications"     desc="Send system notifications via email" />
                  <Toggle checked={!!cfg.notify_sms_enabled}      onChange={v => setC('notify_sms_enabled', v)}      label="SMS Notifications"       desc="Send SMS reminders and alerts (requires SMS provider in Integrations)" />
                  <Toggle checked={!!cfg.notify_inapp_enabled}    onChange={v => setC('notify_inapp_enabled', v)}    label="In-App Notifications"    desc="Show notifications inside the platform" />
                </div>

                <p className={sectionHd}>Notification Triggers</p>
                <div className="space-y-3">
                  <Toggle checked={!!cfg.notify_appointment_reminders}  onChange={v => setC('notify_appointment_reminders', v)}  label="Appointment Reminders"       desc="Remind staff and participants before scheduled appointments" />
                  <Toggle checked={!!cfg.notify_plan_expiry_alerts}      onChange={v => setC('notify_plan_expiry_alerts', v)}      label="Support Plan Expiry Alerts"  desc="Alert when a participant's NDIS plan is approaching expiry" />
                  <Toggle checked={!!cfg.notify_overdue_payment_alerts}  onChange={v => setC('notify_overdue_payment_alerts', v)}  label="Overdue Payment Alerts"      desc="Notify finance team when invoices become overdue" />
                  <Toggle checked={!!cfg.notify_budget_alerts}           onChange={v => setC('notify_budget_alerts', v)}           label="Budget Utilisation Alerts"   desc="Alert when participant budgets reach a threshold" />
                </div>

                <p className={sectionHd}>Reminder Timing</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="Reminder Lead Time (hours)" hint="How many hours before an appointment to send reminders">
                    <input className={inputCls} type="number" min={1} max={168} value={cfg.notify_reminder_hours_before ?? 24} onChange={e => setC('notify_reminder_hours_before', parseInt(e.target.value))} />
                  </Field>
                </div>
              </div>
            )}

            {/* ── 8.6 Security & Access ─────────────────────────────────────── */}
            {tab === 'security' && (
              <div className="p-6 space-y-6">
                <p className={sectionHd}>Session Security</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="Session Timeout (minutes)" hint="Users are automatically logged out after this period of inactivity">
                    <input className={inputCls} type="number" min={5} max={1440} value={cfg.session_timeout_minutes ?? 60} onChange={e => setC('session_timeout_minutes', parseInt(e.target.value))} />
                  </Field>
                  <Field label="Max Login Attempts" hint="Account is locked after this many consecutive failed logins">
                    <input className={inputCls} type="number" min={1} max={20} value={cfg.max_login_attempts ?? 5} onChange={e => setC('max_login_attempts', parseInt(e.target.value))} />
                  </Field>
                </div>

                <p className={sectionHd}>Password Policy</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="Minimum Password Length">
                    <input className={inputCls} type="number" min={6} max={32} value={cfg.password_min_length ?? 8} onChange={e => setC('password_min_length', parseInt(e.target.value))} />
                  </Field>
                </div>
                <div className="space-y-3">
                  <Toggle checked={!!cfg.password_require_uppercase} onChange={v => setC('password_require_uppercase', v)} label="Require uppercase letter"  desc="Password must contain at least one uppercase character" />
                  <Toggle checked={!!cfg.password_require_numbers}   onChange={v => setC('password_require_numbers', v)}   label="Require number"            desc="Password must contain at least one digit" />
                  <Toggle checked={!!cfg.password_require_symbols}   onChange={v => setC('password_require_symbols', v)}   label="Require special character" desc="Password must contain at least one symbol (e.g. ! @ # $)" />
                </div>

                <p className={sectionHd}>Advanced Access</p>
                <div className="space-y-3">
                  <Toggle checked={!!cfg.mfa_enabled} onChange={v => setC('mfa_enabled', v)}
                    label="Multi-Factor Authentication (MFA)"
                    desc="Require a second verification step for all user logins" />
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2 text-sm text-amber-800">
                  <Info className="h-4 w-4 flex-shrink-0 mt-0.5 text-amber-600" />
                  Security settings work together with Roles &amp; Permissions to control what users can access. Changes take effect at the next user login.{' '}
                  <button onClick={() => navigate('/roles')} className="underline font-medium ml-0.5">Manage roles →</button>
                </div>
              </div>
            )}

            {/* ── 8.7 Integrations ─────────────────────────────────────────── */}
            {tab === 'integrations' && (
              <div className="p-6 space-y-6">
                <p className={sectionHd}>NDIS Platform Integrations</p>
                <div className="space-y-3">
                  <IntegrationCard
                    name="PRODA / NDIA Portal"
                    desc="Connect to the National Disability Insurance Agency provider portal for claims and plan management."
                    enabled={!!cfg.enable_proda_integration}
                    onToggle={v => setC('enable_proda_integration', v)}
                    badge="NDIS"
                    color="purple"
                  />
                  <IntegrationCard
                    name="PACE System"
                    desc="Integrate with the NDIS PACE system for up-to-date pricing catalogues and service bookings."
                    enabled={!!cfg.enable_pace_integration}
                    onToggle={v => setC('enable_pace_integration', v)}
                    badge="NDIS"
                    color="purple"
                  />
                </div>

                <p className={sectionHd}>Accounting & Finance</p>
                <div className="space-y-3">
                  <IntegrationCard
                    name="MYOB"
                    desc="Sync invoices, payments, and chart of accounts with MYOB AccountRight or Essentials."
                    enabled={!!cfg.integration_myob_enabled}
                    onToggle={v => setC('integration_myob_enabled', v)}
                    badge="Accounting"
                    color="green"
                  />
                  <IntegrationCard
                    name="Xero"
                    desc="Push invoices and reconcile payments with Xero accounting software."
                    enabled={!!cfg.integration_xero_enabled}
                    onToggle={v => setC('integration_xero_enabled', v)}
                    badge="Accounting"
                    color="green"
                  />
                </div>

                <p className={sectionHd}>Communication Services</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="SMS / Communication Provider" hint="Used for SMS notifications and appointment reminders">
                    <select className={selectCls} value={cfg.integration_communication_provider || ''} onChange={e => setC('integration_communication_provider', e.target.value || null)}>
                      <option value="">None</option>
                      {['Twilio','MessageBird','AWS SNS','Vonage','Infobip'].map(p => <option key={p}>{p}</option>)}
                    </select>
                  </Field>
                </div>

                <p className={sectionHd}>Payment Services</p>
                <div className="grid grid-cols-2 gap-5">
                  <Field label="Payment Provider" hint="Used to process participant and payer payments">
                    <select className={selectCls} value={cfg.integration_payment_provider || ''} onChange={e => setC('integration_payment_provider', e.target.value || null)}>
                      <option value="">None</option>
                      {['Stripe','Square','Tyro','Ezidebit','Eway'].map(p => <option key={p}>{p}</option>)}
                    </select>
                  </Field>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 flex items-start gap-2 text-sm text-slate-600">
                  <Info className="h-4 w-4 flex-shrink-0 mt-0.5 text-slate-400" />
                  Enabling an integration here activates the connection. Full configuration (API keys, credentials) is managed securely by your system administrator.
                </div>
              </div>
            )}

          </div>
        )}

        {can('settings:edit') && <SaveBar dirty={dirty} saving={saving} onSave={handleSave} onReset={handleReset} />}

      </div>
    </Layout>
  )
}

// ── Integration card ────────────────────────────────────────────────────────────
function IntegrationCard({ name, desc, enabled, onToggle, badge, color }: {
  name: string; desc: string; enabled: boolean; onToggle: (v: boolean) => void;
  badge: string; color: 'purple' | 'green' | 'blue';
}) {
  const badgeCls = {
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    green:  'bg-emerald-50 text-emerald-700 border-emerald-200',
    blue:   'bg-blue-50 text-blue-700 border-blue-200',
  }[color]

  return (
    <div className={`flex items-start gap-4 p-4 rounded-xl border transition-colors ${enabled ? 'border-purple-200 bg-purple-50/40' : 'border-slate-200 bg-white'}`}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-sm font-semibold text-slate-800">{name}</p>
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wide ${badgeCls}`}>{badge}</span>
          {enabled && <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded uppercase tracking-wide">Active</span>}
        </div>
        <p className="text-xs text-slate-500">{desc}</p>
      </div>
      <div className="flex-shrink-0 pt-0.5">
        <label className="relative cursor-pointer">
          <div className={`w-9 h-5 rounded-full transition-colors ${enabled ? 'bg-purple-700' : 'bg-slate-200'}`} onClick={() => onToggle(!enabled)} />
          <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${enabled ? 'translate-x-4' : ''}`} />
        </label>
      </div>
    </div>
  )
}
