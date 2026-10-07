import importlib
need = {
    "app.core.ratelimit": ["RateLimiter", "client_ip"],
    "app.core.llm": ["llm_available"],
    "app.core.scheduler": ["price_loop"],
    "app.db.database": ["Base", "SessionLocal", "engine", "get_db"],
    "app.db.seed": ["seed_user_permissions"],
    "app.agents.shopping": ["is_safe_url", "parse_price"],
    "app.agents.textutils": ["top_chunks"],
}
for mod, names in need.items():
    try:
        m = importlib.import_module(mod)
    except Exception as e:
        print("MODULE PROBLEM:", mod, "->", e)
        continue
    for n in names:
        if not hasattr(m, n):
            print("MISSING:", mod, "->", n)
print("check done")