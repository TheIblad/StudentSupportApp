import { createClient } from '@supabase/supabase-js'
const supabaseUrl = 'https://iqmadbkvgmeumaxyntai.supabase.co'
const supabaseKey = 'sb_publishable_C_RfgC2pbT_-dECn2UiWKw_45ilAvbh' // This is safe to be public

export const supabase = createClient(supabaseUrl, supabaseKey)