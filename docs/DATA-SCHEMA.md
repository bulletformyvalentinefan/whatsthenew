# Esquema de datos — whatsthenew

Cada dato (`Item`) lleva **siempre** de dónde salió y cuándo se consultó, además de cuándo se
publicó. Esto hace el reporte **trazable**.

## `Item`

| Campo | Tipo | Descripción |
|---|---|---|
| `category` | str | `jobs` \| `news` \| `company_blog` \| `reddit` \| `roadmap` |
| `source` | str | Dominio o id de la fuente (ej: `seek.com.au`) |
| `source_type` | str | `api` \| `rss` \| `html` \| `xml` \| `reddit` \| `pullpush` |
| `url` | str | Enlace directo al dato |
| `title` | str | Título del aviso/post |
| `company` | str | Empresa (si aplica) |
| `location` | str | Ubicación |
| `remote` | bool \| null | Remoto / híbrido / desconocido |
| `role` | str | Rol clasificado |
| `level` | str | `junior` \| `semi` \| `senior` \| `lead` \| `staff` \| `principal` \| `""` |
| `years` | list[int] | Años de experiencia mencionados |
| `skills` | list[str] | Stack detectado |
| `salary` | str | Sueldo (si la fuente lo trae) |
| `applicants` | str | Postulantes (raro; casi ninguna fuente lo publica) |
| `posted_at` | str | Fecha de publicación del dato |
| `fetched_at` | str | **Fecha de consulta** (dd/mm/aaaa hh:mm, zona local) |
| `query` | str | Consulta usada para obtenerlo |
| `replies` | int | Nº de respuestas del hilo (Reddit) |
| `has_replies` | bool | Si el hilo tiene respuestas (Reddit) |
| `excerpt` | str | Primeros ~2000 caracteres del texto |

## JSON crudo (temporal)

`/tmp/whatsthenew_raw.json`

```json
{
  "meta": {
    "generated_at": "17/10/2026 15:40",
    "count": 123,
    "user_agent": "whatsthenew/0.1 ..."
  },
  "items": [ { "category": "jobs", "source": "getonbrd.com", "...": "..." } ]
}
```

Se borra al terminar la corrida (fase de purga).

## Reporte de salida

`output/PROPOSED_UPDATES.md` — agrupado por **rol** y **nivel**, con el **delta** junior vs senior y
la fuente + fecha de cada fila. Peso objetivo: **< 10 KB**.
