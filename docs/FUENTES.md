# Fuentes — whatsthenew

Todas las fuentes fueron **verificadas con `curl`** el 17/10/2026. Regla: **feed/API primero**, HTML
solo si no hay otra opción. Pausas: **4 s** entre peticiones; **10 s** en Reddit.

## Empleos — Global / USA / Europa / Australia (sin API key)

| Fuente | Endpoint | Mercado | Formato | Estado |
|---|---|---|---|---|
| WeWorkRemotely | `weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss` | Global remoto | RSS | ✅ 200 |
| Seek | `seek.com.au/api/jobsearch/v5/search?keywords={q}&page={p}` | Australia | JSON | ✅ 200 (la web da 403) |
| Jobicy | `jobicy.com/api/v2/remote-jobs?count=50&tag={tag}` | Global remoto | JSON | ✅ 200 |
| Working Nomads | `workingnomads.com/api/exposed_jobs/` | Global remoto | JSON | ✅ 200 |
| Landing.jobs | `landing.jobs/api/v1/jobs` | Europa | JSON | ✅ 200 |
| Himalayas | `himalayas.app/jobs/api?limit=100` | Global remoto | JSON | ✅ 200 |
| RemoteOK | `remoteok.com/api` | Global remoto | JSON | ✅ 200 |
| Remotive | `remotive.com/api/remote-jobs?search={q}` | Global remoto | JSON | ✅ 200 |
| HN "Who is hiring" | `hn.algolia.com/api/v1/search?query={q}&tags=comment` | Global | JSON | ✅ 200 |
| Jora AU | `au.jora.com/jobs?q={q}` | Australia | HTML | ✅ 200 |
| Dice | `dice.com/jobs?q={q}` | USA | HTML | ✅ 200 |
| BuiltIn | `builtin.com/jobs` | USA | HTML | ✅ 200 (desactivado por defecto) |
| The Muse | `themuse.com/api/public/jobs?page=1` | Global | JSON | ⚠️ inestable |

## Empleos — Chile

| Fuente | Endpoint | Formato | Estado |
|---|---|---|---|
| **GetOnBrd** | `getonbrd.com/jobs/feed.atom` | XML (`<job>`) | ✅ 200 — **fuente principal** |
| Computrabajo | `cl.computrabajo.com/trabajo-de-{q}` | HTML | ✅ 200 (sin RSS) |
| Laborum | `laborum.cl/` | HTML | ✅ 200 (sin RSS) |
| Trabajando | `trabajando.cl/` | HTML | ✅ 200 (sin RSS) |
| Chiletrabajos | `chiletrabajos.cl/` | HTML | ✅ 200 (su `/rss` no es real) |
| BNE | `bne.cl/` | HTML | ✅ 200 (fuente oficial) |

## Noticias

`thenewstack.io/feed/`, `feed.infoq.com/`, `techcrunch.com/feed/` (EN) ·
`feeds.weblogssl.com/genbeta`, `feeds.weblogssl.com/xataka2` (ES) · HN front page (JSON).

## Blogs de empresas

AWS DevOps (`aws.amazon.com/blogs/devops/feed/`), Netflix (`netflixtechblog.com/feed`),
Meta (`engineering.fb.com/feed/`). **Pendiente:** Google Cloud y Mercado Libre Tech (localizar feed).

## Roadmaps / skills

roadmap.sh (repo `nilbuild/developer-roadmap`), dev.to API, GitHub Trending.

## Reglas anti-bloqueo

- Feed/API primero; respetar `robots.txt`; User-Agent honesto con contacto.
- Pausa 4 s (10 s Reddit). GitHub sin token: 60 req/h.
- **No automatizar:** LinkedIn, Indeed, Computrabajo-API, `devops.com` (403).
- Reddit: usar **app OAuth** (100 req/min). `.json` sin token da 403; `.rss` da 429 en ráfaga.
