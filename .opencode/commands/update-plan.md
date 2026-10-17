---
description: Actualiza el plan de carrera a partir de los datos de mercado
agent: plan-updater
---

El archivo de datos crudos está en `$1` (por defecto: `/tmp/whatsthenew_raw.json`) y el plan en
`GOD_PLAN.md`.

1. Lee el JSON crudo y `GOD_PLAN.md`.
2. Clasifica por rol y nivel (sin excluir nada).
3. Resume el mercado por rol/nivel: años, stack, sueldos, ubicación, remoto.
4. Marca el delta junior → senior de cada rol.
5. Compara con el plan y propón cambios concretos.
6. Escribe `output/PROPOSED_UPDATES.md` (reporte, máximo 2 páginas) con fuente
   (dominio + URL) y fecha de consulta (dd/mm/aaaa hh:mm) en cada fila.
7. Escribe `output/GOD_PLAN.proposed.md`: el plan completo ya actualizado, que es
   lo que el pipeline convertirá en Pull Request.

No hagas `git push`. En español.
