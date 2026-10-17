# Protección de la rama `main`

La rama `main` queda **protegida** para que nadie haga `push` directo: todo cambio entra por Pull
Request. Como el proyecto es individual, se permite fusionar **sin aprobación de terceros** (para no
bloquearte), pero sí se exige PR, se prohíbe el `force-push` y se prohíbe borrar la rama.

## Reglas aplicadas

| Regla | Valor | Motivo |
|---|---|---|
| Requerir Pull Request | sí | Nada entra directo a `main` |
| Aprobaciones requeridas | 0 | Proyecto individual (puedes fusionar tu propio PR) |
| Bloquear force-push | sí | No reescribir historia |
| Bloquear borrado | sí | La rama no se puede eliminar |
| Requerir historial lineal | sí | Commits encima, sin merges sucios |

## Cómo se aplica

Con GitHub CLI (ya autenticado):

```bash
./scripts/protect-branch.sh
```

El script usa la API de **rulesets**, que permite proteger `main` incluso **antes** de que la rama
exista en el remoto (no requiere un push previo).

### Alternativa: interfaz web

`Settings → Branches → Add branch protection rule → Branch name pattern: main` y activar las
opciones de la tabla de arriba.

## Deshacer

```bash
gh api --method DELETE repos/bulletformyvalentinefan/whatsthenew/rulesets/<id>
```

## Notas

- Las **reglas de ruleset** no dependen del contenido local; solo cambian la configuración del repo.
- Este documento describe la intención del proyecto; `scripts/protect-branch.sh` la aplica.
