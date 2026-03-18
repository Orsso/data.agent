# BUGLOG — Anomalies trouvées lors de l'écriture des tests

## [FIXED] — `_detect_format` ne fonctionnait pas avec pandas 3.x (dtype "str")
- **Fichier** : core/profiler.py
- **Ligne(s)** : ~L60-L61
- **Constaté** : La fonction commençait par `if series.dtype != "object": return None`. En pandas 3.x, le dtype par défaut des colonnes texte est `"str"` et non `"object"`. Aucun format n'était détecté.
- **Fix** : `series.dtype not in ("object", "str", "string")` — accepte les 3 variantes de dtype texte.
- **Test** : `test_default_string_dtype_is_detected` vérifie le fix.

---

## [ODDITY] — `_format_output` : priorité implicite dans la chaîne elif
- **Fichier** : core/tools/execute_python.py
- **Ligne(s)** : ~L113-L142
- **Constaté** : Quand `result` est `None` mais `card_updates` ET `cards` sont tous les deux non-vides, seul le message `card_updates` est affiché. Le message `cards` est dans un `elif` et ne sera jamais atteint dans ce cas.
- **Attendu** : Comportement probablement voulu (card_updates a la priorité), mais pas documenté.
- **Impact sur les tests** : Aucun — on teste chaque branche isolément.
- **Sévérité** : **cosmétique**

---

## [ODDITY] — `todo` tool : fallback `task` quand `content` est vide
- **Fichier** : core/tools/todo.py
- **Ligne(s)** : ~L39
- **Constaté** : `content = item.get("content") or item.get("task", "")` — un item avec `{"content": "", "task": "real task"}` utilisera `"real task"` car la chaîne vide est falsy en Python.
- **Attendu** : Incertain — est-ce que `content: ""` devrait être traité comme "pas de contenu" ou comme "contenu explicitement vide" ?
- **Impact sur les tests** : Test `test_write_uses_task_fallback` vérifie ce comportement. Documenté ici au cas où ce serait non-intentionnel.
- **Sévérité** : **mineur**

---

## [ODDITY] — `_detect_format` : seuil strict pour petits datasets
- **Fichier** : core/profiler.py
- **Ligne(s)** : ~L66-L89
- **Constaté** : Le seuil de détection currency est `> 0.5` (strict). Pour un dataset de 2 lignes avec 1 valeur currency, le ratio est 0.5 exactement, donc non détecté. C'est mathématiquement correct mais potentiellement surprenant pour de petits fichiers.
- **Attendu** : Comportement correct, mais pourrait être documenté.
- **Impact sur les tests** : Test `test_currency_below_threshold` vérifie explicitement ce cas limite.
- **Sévérité** : **cosmétique**
