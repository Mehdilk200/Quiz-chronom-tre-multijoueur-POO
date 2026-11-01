
# Support de travail en équipe

## Objectif du projet

Le projet est un quiz multijoueur local avec deux interfaces : une version console
(`quiz.py`) et une interface Streamlit (`app.py`). Les deux interfaces réutilisent les
mêmes classes métier : questions, joueurs, jokers et classement.

La séparation recommandée pour une équipe de trois personnes est organisée par
responsabilité. Chaque membre est propriétaire des fichiers indiqués dans sa partie et
préviens l'équipe avant de modifier un contrat utilisé par les autres.

## Répartition proposée

### Membre 1 — Questions et contexte

**Fichiers principaux :** `question.py`, `question_bank.py`, `question_context.py`,
`questions.json`.

**Responsabilités :** représenter une question, charger les questions JSON, tirer les
questions d'une catégorie et garder l'état de la question en cours.

- `Question` (`question.py`) : stocke l'énoncé (`text`), les propositions (`choices`) et
  l'indice de la bonne réponse (`answer`). Le `__init__` est généré par `@dataclass`.
- `Question.shuffled()` : mélange les propositions et retourne une nouvelle question en
  recalculant l'indice de la bonne réponse. L'objet original n'est pas modifié.
- `QuestionBank` (`question_bank.py`) : charge les questions depuis un fichier JSON et
  les organise par catégorie.
- `QuestionBank.__init__(path)` : lit le JSON et construit les objets `Question`.
- `QuestionBank.categories` : propriété qui retourne la liste des catégories chargées.
- `QuestionBank.draw(category, n)` : tire `n` questions dans la catégorie et mélange les
  propositions de chaque question. Si `n` dépasse la taille de la catégorie, il reprend
  un nouveau tirage dans la banque.
- `QuestionContext` (`question_context.py`) : conserve l'état d'une question pendant la
  réponse. `question` est la question active, `hidden` contient les indices masqués par
  un joker et `passed` indique si la question a été passée. Son `__init__` est généré par
  `@dataclass`.

**À vérifier :** la structure de `questions.json`, les indices de réponse (`answer`, à
partir de zéro), le mélange des propositions et les tirages de taille supérieure à une
catégorie.

### Membre 2 — Joueurs, jokers et classement

**Fichiers principaux :** `player.py`, `joker.py`, `leaderboard.py`.

**Responsabilités :** gérer le score et les jokers de chaque joueur, appliquer les effets
des jokers et enregistrer les résultats d'une partie.

- `Joker` (`joker.py`) : classe abstraite commune aux jokers. `key` est la touche utilisée,
  `label` le nom affiché et `used` indique si le joker a déjà servi.
- `Joker.__init__()` : initialise `used` à `False`.
- `Joker.apply(ctx)` : méthode abstraite ; chaque joker concret doit appliquer son effet
  au `QuestionContext` et retourner un message.
- `FiftyFifty.apply(ctx)` : masque jusqu'à deux mauvaises réponses encore visibles.
- `Pass.apply(ctx)` : marque la question comme passée avec `ctx.passed = True`.
- `Player` (`player.py`) : représente un joueur avec son nom, son score et ses jokers.
- `Player.__init__(name)` : initialise le joueur à zéro point et lui donne un joker 50/50
  et un joker Passer.
- `Player.available_jokers()` : retourne les jokers qui n'ont pas encore été utilisés.
- `Player.add_points(pts)` : ajoute `pts` au score du joueur.
- `Leaderboard` (`leaderboard.py`) : lit, met à jour et affiche les statistiques
  persistantes des joueurs.
- `Leaderboard.__init__(path)` : charge le classement JSON existant ; si le JSON est
  invalide, démarre avec un classement vide.
- `Leaderboard.record(players)` : ajoute les points, le nombre de parties et les victoires
  de chaque joueur, puis écrit le fichier JSON. En cas d'égalité au meilleur score, chaque
  joueur à égalité reçoit une victoire.
- `Leaderboard.show(top=10)` : affiche les `top` joueurs classés par total de points.

**Fonctions Streamlit liées à cette responsabilité dans `app.py` :**

- `resolve(result, chosen=None)` : termine la question, mémorise le résultat et attribue
  les points et le bonus de temps en cas de bonne réponse.
- `on_answer(i)` : ignore une réponse si la question est déjà terminée ou si le temps est
  écoulé ; sinon, compare l'indice choisi à la bonne réponse.
- `on_joker(key)` : vérifie que la question et le joker sont encore actifs, puis applique
  le joker sélectionné.
- `scoreboard(g)` : affiche les scores et met en évidence le joueur qui répond.
- `leaderboard_table()` : affiche le classement persistant dans le tableau Streamlit.

**À vérifier :** un joker ne peut être utilisé qu'une fois par joueur, un joker 50/50 ne
masque jamais la bonne réponse et une partie terminée est enregistrée une seule fois.

### Membre 3 — Déroulement, console et interface graphique

**Fichiers principaux :** `quiz_game.py`, `timed_input.py`, `settings.py`, `quiz.py`,
`app.py`.

**Responsabilités :** assembler les composants métier, gérer les tours et le chronomètre,
puis afficher les écrans console et Streamlit. Le fichier `app.py` est partagé par plusieurs
responsabilités : ce membre coordonne son intégration pour limiter les conflits.

- `QuizGame` (`quiz_game.py`) : pilote une partie en console. Ses constantes définissent la
  durée d'une question, le nombre de questions par joueur et le barème.
- `QuizGame.__init__(bank, leaderboard)` : reçoit la banque de questions et le classement,
  puis initialise la liste des joueurs.
- `QuizGame.setup()` : demande le nombre de joueurs, leurs noms et la catégorie ; retourne
  la catégorie choisie.
- `QuizGame.run()` : prépare les questions, distribue les tours aux joueurs, appelle
  `ask()` pour chaque question et finit la partie.
- `QuizGame.ask(player, question)` : gère la réponse chronométrée, les jokers, le calcul du
  score et les messages de résultat pour une question.
- `QuizGame._display(ctx, player)` : affiche l'énoncé, les propositions visibles et les
  jokers encore disponibles.
- `QuizGame.finish()` : affiche les scores finaux, enregistre la partie et affiche le
  classement général.
- `timed_input(prompt, deadline)` (`timed_input.py`) : lit une réponse au clavier jusqu'à
  une échéance. Dans un terminal, affiche le compte à rebours ; sans terminal, utilise la
  saisie standard. La fonction interne `render(buf)` rafraîchit l'affichage du compte à
  rebours.
- `settings.py` : définit `BASE_DIR`, le chemin du dossier du projet, et `LETTERS`, les
  lettres utilisées pour identifier les réponses.
- `main()` (`quiz.py`) : construit la banque et le classement, lance les parties console
  et propose de rejouer. `quiz.py` ré-exporte aussi les classes pour préserver les imports
  utilisés par `app.py`.

**Fonctions Streamlit dans `app.py` :**

- `md_escape(text)` : échappe les caractères spéciaux avant d'afficher du texte en
  Markdown.
- `nbsp_punct(text)` : ajoute un espace insécable avant certaines ponctuations dans les
  questions.
- `game()` : récupère l'état courant du jeu dans la session Streamlit.
- `current_player(g)` : retourne le joueur dont c'est le tour.
- `start_game(names, category, seconds, per_player)` : crée les joueurs, tire les
  questions et initialise l'état de la partie.
- `on_next()` : avance à la question suivante ou passe à l'écran des résultats ; enregistre
  le classement à la fin de la partie.
- `on_restart()` : efface l'état de la partie et retourne à l'écran de configuration.
- `timer_bar(remaining, total)` : affiche la barre visuelle du chronomètre.
- `timer_fragment()` : actualise le chronomètre chaque seconde et déclenche le timeout si
  le temps est écoulé.
- `setup_view()` : affiche le formulaire de configuration et l'accès au classement.
- `game_view()` : affiche la question active, les propositions, les jokers et le résultat.
- `results_view()` : affiche le podium, le classement général et le bouton pour rejouer.
- Le routeur en fin de fichier choisit l'écran Streamlit selon la phase (`setup`, `game`
  ou `results`).

**À vérifier :** le jeu console peut démarrer avec `python3 quiz.py`, l'interface démarre
avec `streamlit run app.py`, et les deux interfaces utilisent les mêmes règles de score et
les mêmes classes métier.

## Flux général

```text
questions.json -> QuestionBank -> Question -> QuizGame ou app.py
                                      |
                                      v
                            QuestionContext <- Joker
                                      |
Player -> score et jokers -> Leaderboard -> leaderboard.json
```

`quiz.py` est le point d'entrée de la console et une façade d'import. Les classes restent
définies dans leurs propres modules ; `app.py` importe leur façade depuis `quiz.py`.

## Conseils pour travailler ensemble

1. Répartissez les fichiers selon les trois rôles ci-dessus et désignez une personne pour
   intégrer les changements dans `app.py`.
2. Avant de modifier une signature ou une structure partagée, annoncez-la à l'équipe.
   Exemples : les champs de `Question`, les clés du dictionnaire de session Streamlit, ou
   les paramètres de `Leaderboard.record()`.
3. Gardez les imports entre modules cohérents et lancez les commandes depuis la racine du
   projet. Utilisez les modules dédiés pour le développement ; gardez les imports existants
   depuis `quiz.py` quand une interface en dépend.
4. Travaillez sur des branches séparées, avec un nom clair. Faites des commits petits et
   descriptifs, puis fusionnez d'abord les modules métier et ensuite l'interface.
5. Ne modifiez pas `leaderboard.json` pendant les tests d'intégration sans sauvegarde ;
   préférez un fichier temporaire pour tester l'enregistrement.
6. Après une modification, vérifiez au minimum la compilation et les deux chemins
   d'exécution pertinents :

   ```bash
   python3 -m py_compile quiz.py settings.py timed_input.py question.py question_bank.py question_context.py joker.py player.py leaderboard.py quiz_game.py app.py
   python3 quiz.py
   streamlit run app.py
   ```
7. Testez aussi les cas limites : noms de joueurs identiques, catégories valides, joker
   déjà utilisé, bonne et mauvaise réponse, timeout, égalité au classement et partie
   rejouée.

## Lancement du projet

Depuis la racine du projet :

```bash
pip install -r requirements.txt
python3 quiz.py
```

Pour lancer l'interface graphique :

```bash
streamlit run app.py
```
