/**
 * Global field-level error handling — single consistent way to read backend
 * errors across the whole app.
 *
 * The backend (see app/core/exceptions.py on the server) always responds to
 * a failed request with:
 *
 *   {
 *     "detail": string | Array<{ loc, msg }>,   // unchanged — existing code
 *                                                //   reading `detail` keeps working
 *     "field_errors"?: { [fieldName: string]: string }  // NEW
 *   }
 *
 * `field_errors` is present whenever at least one error can be tied to a
 * specific request field (a duplicate ABN, an invalid format, a business
 * rule about one field's value, etc). Use the helpers below instead of
 * reading `err.response.data.detail` directly, so every form in the app
 * shows field errors the same way: beside the field when it's rendered on
 * the current screen, falling back to one generic message otherwise.
 */
import type { AxiosError } from 'axios'

const DEFAULT_FALLBACK = 'Something went wrong. Please try again.'

/** Raw field_errors map from a failed request, or {} if none. */
export function getFieldErrors(err: unknown): Record<string, string> {
  const data = (err as AxiosError)?.response?.data as any
  const fe = data?.field_errors
  return fe && typeof fe === 'object' ? fe : {}
}

/** Human-readable fallback message — used when no field_errors apply, or as the generic banner text. */
export function getGenericErrorMessage(err: unknown, fallback: string = DEFAULT_FALLBACK): string {
  const data = (err as AxiosError)?.response?.data as any
  const detail = data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d: any) => d?.msg ?? String(d)).join(' ')
  }
  return (err as any)?.message || fallback
}

/**
 * The one function every form's onError handler should call.
 *
 * Give it the list of field names your form actually renders (must match
 * the backend's field name exactly, e.g. "abn", "branch_code", "email").
 * It splits the backend's field_errors into:
 *   - fieldErrors: a map of only the fields present on THIS screen, ready to
 *     pass straight into each field's `error` prop so the message renders
 *     directly beside/below that field.
 *   - genericMessage: a fallback string for anything that couldn't be
 *     attached to a field on this screen (e.g. the backend error is about a
 *     field that isn't rendered here) — show this in your existing generic
 *     error banner/toast, or null if every error was successfully attached
 *     to a field.
 *
 * Example:
 *   onError: (err) => {
 *     const { fieldErrors, genericMessage } = splitFieldErrors(err, ['abn', 'organisation_name'])
 *     setFieldErrors(fieldErrors)
 *     setGenericError(genericMessage)
 *   }
 */
export function splitFieldErrors(
  err: unknown,
  knownFields: readonly string[],
  fallback: string = DEFAULT_FALLBACK,
): { fieldErrors: Record<string, string>; genericMessage: string | null } {
  const all = getFieldErrors(err)

  if (Object.keys(all).length === 0) {
    // No structured field_errors at all (infra error, unhandled exception, etc.)
    return { fieldErrors: {}, genericMessage: getGenericErrorMessage(err, fallback) }
  }

  const fieldErrors: Record<string, string> = {}
  const leftover: string[] = []
  for (const [field, msg] of Object.entries(all)) {
    if (knownFields.includes(field)) fieldErrors[field] = msg
    else leftover.push(msg)
  }

  return {
    fieldErrors,
    genericMessage: leftover.length > 0 ? leftover.join(' ') : null,
  }
}
