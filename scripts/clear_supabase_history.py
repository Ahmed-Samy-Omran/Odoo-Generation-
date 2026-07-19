from app.services.supabase_service import supabase_service

if not supabase_service.is_enabled():
    print('Supabase not enabled or credentials missing.')
    raise SystemExit(1)

for table in ['generation_jobs', 'chat_history']:
    try:
        sel = supabase_service.client.table(table).select('*').execute()
        rows = getattr(sel, 'data', []) or []
        print(f"{table} rows before delete: {len(rows)}")
        res = supabase_service.client.table(table).delete().execute()
        resp_data = getattr(res, 'data', None)
        print(f"{table} delete response data: {resp_data}")
        sel2 = supabase_service.client.table(table).select('*').execute()
        rows2 = getattr(sel2, 'data', []) or []
        print(f"{table} rows after delete: {len(rows2)}")
    except Exception as e:
        print(f"Error operating on {table}: {e}")
