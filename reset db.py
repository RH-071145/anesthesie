from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:dYSOklTNgPJSAZnRqvufZyIMQdeQAzdX@mainline.proxy.rlwy.net:24579/railway')
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS recommandations_pre CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS examen_complet CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS donnees_paracliniques CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS evaluation_preop CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS patient CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS "user" CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS doctors CASCADE'))
    conn.commit()
print('Done!')