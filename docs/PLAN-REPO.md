# El repositorio privado del plan — whatsthenew

El plan de carrera (`GOD_PLAN.md`) es personal y vive en **su propio repositorio
privado**, nunca en este repo público. Así puedes versionarlo, revisar propuestas
como Pull Requests y fusionarlas, sin exponerlo.

## Por qué un repositorio aparte

Un archivo ignorado (`.gitignore`) **no existe** para GitHub: no se puede proponer
un cambio sobre él con un PR ni "fusionarlo". Para tener el flujo *propuesta → revisión
→ merge* hace falta que el plan esté **versionado**, y para que nadie lo vea, en un
repositorio **privado**.

## Estructura del repo privado

```text
god-plan/                  (privado)
├── GOD_PLAN.md            # tu plan (fuente de verdad)
├── proposals/
│   └── proposal-2026-W42.md   # el porqué de cada propuesta de esa semana
└── README.md
```

## Crearlo (una sola vez)

```bash
# Crea el repo privado y sube tu plan
gh repo create bulletformyvalentinefan/god-plan --private --clone
cd god-plan
cp ~/Desktop/god_plan.md GOD_PLAN.md
printf '# god-plan\n\nPlan de carrera privado. Las propuestas llegan como Pull Requests.\n' > README.md
git add GOD_PLAN.md README.md
git commit -m "chore: plan inicial"
git push -u origin main
```

Añade protección a `main` para que toda propuesta pase por PR (opcional pero
recomendado):

```bash
gh api -X PUT repos/bulletformyvalentinefan/god-plan/branches/main/protection \
  --input - <<'JSON'
{
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
```

## El token

El pipeline necesita **leer y proponer** en ese repo. Crea un **token fine-grained**
(GitHub → Settings → Developer settings → Fine-grained tokens):

- **Repository access:** solo `bulletformyvalentinefan/god-plan`.
- **Permissions:** `Contents: Read and write` y `Pull requests: Read and write`.

Guárdalo en el `.env` del servidor como `PLAN_REPO_TOKEN=...`. **Nunca** en el repo
público: `.env` está ignorado y `scripts/check-secrets.sh` lo vigila.

## El flujo semanal

```text
1. El pipeline clona el repo privado en /tmp/whatsthenew-plan (efímero).
2. OpenCode lee GOD_PLAN.md + los datos de mercado.
3. Escribe:
     output/PROPOSED_UPDATES.md       (el reporte razonado)
     output/GOD_PLAN.proposed.md      (el plan completo ya actualizado)
4. El pipeline crea la rama  proposal/AAAA-Wss  y sustituye GOD_PLAN.md
   por la versión propuesta; añade el reporte en proposals/AAAA-Wss.md.
5. Hace push y abre un Pull Request contra main.
6. TÚ revisas el diff y fusionas (o cierras) el PR.
7. El clon temporal se borra: no queda el plan en el servidor.
```

El pipeline **nunca** fusiona solo, ni escribe en `main`: **propone, no impone**.

## Qué mirar en el PR

- El **diff de `GOD_PLAN.md`**: lo que cambiaría de verdad.
- `proposals/proposal-AAAA-Wss.md`: el porqué, con fuente y fecha de cada dato.

## Variables de entorno

| Variable | Para qué |
|---|---|
| `PLAN_REPO` | `owner/repo` del repo privado (ej. `bulletformyvalentinefan/god-plan`) |
| `PLAN_REPO_BRANCH` | Rama base del PR (por defecto `main`) |
| `PLAN_REPO_TOKEN` | Token fine-grained con acceso a ese repo |
| `PUBLISH_PROPOSAL` | `1` para abrir el PR automáticamente |
| `PROPOSAL_BRANCH_PREFIX` | Prefijo de la rama (por defecto `proposal`) |
| `PLAN_DIR` | Dónde se clona (efímero, por defecto `/tmp/whatsthenew-plan`) |
