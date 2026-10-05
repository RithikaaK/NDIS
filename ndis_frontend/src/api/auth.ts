import api, { publicApi } from './axios'

export const login          = (data)                    => publicApi.post('/auth/login',         data)
export const sendOtp        = (email)                   => publicApi.post('/auth/send-otp',      { email })
export const verifyOtp      = (email, otp)              => publicApi.post('/auth/verify-otp',    { email, otp })
export const resetPassword  = (email, otp, new_password) => publicApi.post('/auth/reset-password', { email, otp, new_password })

export const getMe                = ()       => api.get('/auth/me')
export const updateMe             = (data)   => api.put('/auth/me',                       data)
export const changePassword       = (data)   => api.put('/auth/me/password',              data)
export const forcedChangePassword = (data)   => api.post('/auth/forced-change-password',  data)
