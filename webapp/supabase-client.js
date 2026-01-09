const SUPABASE_URL = 'https://wpgrollhyfoszmlotfyg.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndwZ3JvbGxoeWZvc3ptbG90ZnlnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc2NDcwNjksImV4cCI6MjA4MzIyMzA2OX0.NQNWmwHxSMtcAUfMee3848r8OccACXhuuZjhvNnw3bM';
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
window.LeadAPI = {
      async login(email, password) { return supabase.auth.signInWithPassword({ email, password }); },
      async signUp(email, password) { return supabase.auth.signUp({ email, password }); },
      async getUser() { const { data } = await supabase.auth.getUser(); return data.user; }
};
