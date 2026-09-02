// typed wrapper — never call window.pywebview.api directly
export async function call(method, payload){
  const api = window.pywebview && window.pywebview.api;
  if(!api || !api[method]) throw new Error("bridge not ready: "+method);
  const res = await api[method](payload ?? null);
  if(!res.ok) throw Object.assign(new Error(res.error.message), res.error);
  return res.data;
}
