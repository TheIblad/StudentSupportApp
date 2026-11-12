import { createClient } from '@supabase/supabase-js'
const supabaseUrl = 'https://lyculuiyuoeitxcmihiz.supabase.co'
const supabaseKey = 'sb_publishable_odqF1jvIUf_Qk-aJou0NhQ_jwGhx-sp' // This is safe to be public

export const supabase = createClient(supabaseUrl, supabaseKey)