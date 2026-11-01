# Le quiz expliqué simplement

## 1. C'est quoi, ce projet ?

Imagine un jeu de questions. Les joueurs répondent chacun leur tour avant la fin du
chronomètre. Ils peuvent utiliser des jokers. À la fin, le jeu garde les scores dans un
fichier.

Il y a deux façons de jouer :

- `quiz.py` : le jeu écrit dans le terminal.
- `app.py` : le jeu s'affiche dans une page web avec Streamlit.

Les deux façons utilisent les mêmes questions, joueurs, jokers et classement.

## 2. Comment le jeu fonctionne ?

```text
┌──────────────────┐
│ questions.json   │  Les questions rangées par catégorie
└────────┬─────────┘
         v
┌──────────────────┐
│ QuestionBank     │  Choisit les questions
└────────┬─────────┘
         v
┌──────────────────┐       ┌──────────────────┐
│ Question         │ <---> │ QuestionContext  │
│ texte + réponses │       │ état de la question│
└────────┬─────────┘       └────────┬─────────┘
         │                          ^
         v                          │ agit sur
┌──────────────────┐       ┌────────┴─────────┐
│ QuizGame / app   │ ----> │ Joker            │
│ montre le jeu    │       │ aide le joueur   │
└────────┬─────────┘       └──────────────────┘
         v
┌──────────────────┐
│ Player           │  Garde le nom et les points
└────────┬─────────┘
         v
┌──────────────────┐
│ Leaderboard      │  Garde les résultats
└────────┬─────────┘
         v
  leaderboard.json
```

En très court : le jeu prend une question, la montre à un joueur, compte ses points,
puis passe au joueur suivant.

## 3. Partage du travail pour trois personnes

```text
                NOTRE ÉQUIPE
                    │
       ┌────────────┼────────────┐
       v            v            v
 LAKHIAL       BELATTAR     BOUTOUCHA
 El Mehdi      Othmane      Ismail
  Questions     Joueurs      Déroulement
  et réponses   et points    et écrans
```

### Lakhial El Mehdi : les questions

**Fichiers :** `question.py`, `question_bank.py`, `question_context.py`, `questions.json`.

Cette personne prépare les cartes de questions et vérifie que les bonnes réponses sont
bien indiquées.

**`Question` dans `question.py`**

C'est une carte de quiz. Elle garde le texte, les réponses possibles et le numéro de la
bonne réponse.

- `Question.__init__(text, choices, answer)` : crée la carte. Python le prépare tout seul
  grâce à `@dataclass`.
- `Question.shuffled()` : mélange les réponses et fabrique une nouvelle carte en gardant
  la bonne réponse correcte.

**`QuestionBank` dans `question_bank.py`**

C'est la boîte qui garde toutes les cartes, rangées par matière ou catégorie.

- `QuestionBank.__init__(path)` : ouvre le fichier JSON et lit les cartes.
- `QuestionBank.categories` : donne la liste des catégories, par exemple Python ou Java.
- `QuestionBank.draw(category, n)` : prend `n` cartes dans la catégorie choisie et mélange
  leurs réponses. S'il faut plus de cartes qu'il y en a dans la boîte, il recommence un
  nouveau tour de tirage.

**`QuestionContext` dans `question_context.py`**

C'est un petit carnet pour la question qui est en train d'être jouée.

- `QuestionContext.__init__(question)` : garde la question active. Python le crée grâce à
  `@dataclass`.
- `hidden` : garde les réponses cachées par le joker 50/50.
- `passed` : dit si le joueur a passé la question.

**À tester :** charger les catégories, tirer des cartes, mélanger les réponses et vérifier
que le numéro de la bonne réponse suit bien son texte.

### Belattar Othmane : les joueurs, les jokers et les scores

**Fichiers :** `player.py`, `joker.py`, `leaderboard.py`.

Cette personne s'occupe du sac à dos de chaque joueur : ses points et ses jokers. Elle
s'occupe aussi du tableau des résultats.

**`Player` dans `player.py`**

C'est la fiche d'un joueur.

- `Player.__init__(name)` : crée le joueur avec son nom, zéro point et deux jokers.
- `Player.available_jokers()` : montre les jokers qui n'ont pas encore servi.
- `Player.add_points(pts)` : ajoute des points au joueur.

**`Joker`, `FiftyFifty` et `Pass` dans `joker.py`**

`Joker` est le modèle commun. Les deux autres classes sont deux sortes de joker.

- `Joker.__init__()` : marque le joker comme non utilisé.
- `Joker.apply(ctx)` : dit aux jokers enfants d'appliquer leur effet. C'est une méthode
  modèle : elle doit être écrite dans chaque vrai joker.
- `FiftyFifty.apply(ctx)` : cache jusqu'à deux mauvaises réponses.
- `Pass.apply(ctx)` : marque la question comme passée.

```text
        Joker (modèle commun)
            /         \
           v           v
   FiftyFifty         Pass
   cache des choix    passe la question
```

**`Leaderboard` dans `leaderboard.py`**

C'est le cahier qui se souvient des résultats même après la fermeture du jeu.

- `Leaderboard.__init__(path)` : ouvre le classement. Si le fichier est cassé ou absent,
  le classement commence vide.
- `Leaderboard.record(players)` : ajoute les résultats des joueurs et écrit le fichier
  `leaderboard.json`. Si plusieurs joueurs sont premiers à égalité, ils gagnent chacun une
  victoire.
- `Leaderboard.show(top=10)` : montre les meilleurs joueurs, jusqu'à dix par défaut.

**Quelques fonctions de `app.py` liées aux joueurs :**

- `resolve(result, chosen=None)` : termine la question et ajoute les points si la réponse
  est bonne.
- `on_answer(i)` : vérifie la réponse choisie par le joueur.
- `on_joker(key)` : lance le joker choisi s'il est encore disponible.
- `scoreboard(g)` : montre les scores à l'écran.
- `leaderboard_table()` : montre le classement dans la page web.

**À tester :** les points augmentent après une bonne réponse, un joker ne sert qu'une fois,
et les résultats apparaissent dans le classement.

### Boutoucha Ismail : le chef d'orchestre et les écrans

**Fichiers :** `quiz_game.py`, `timed_input.py`, `settings.py`, `quiz.py`, `app.py`.

Cette personne fait avancer le jeu : elle prépare les tours, affiche les questions et
utilise les classes des deux autres personnes. Elle coordonne aussi les changements de
`app.py`, car plusieurs parties du projet utilisent ce fichier.

**`QuizGame` dans `quiz_game.py`**

C'est le chef d'orchestre du jeu en console.

- `QuizGame.__init__(bank, leaderboard)` : reçoit la boîte de questions et le cahier des
  scores.
- `QuizGame.setup()` : demande le nombre de joueurs, leurs noms et la catégorie.
- `QuizGame.run()` : démarre la partie, distribue les questions et termine la partie.
- `QuizGame.ask(player, question)` : pose une question, attend la réponse, gère les jokers
  et calcule les points.
- `QuizGame._display(ctx, player)` : montre la question, ses réponses et les jokers.
- `QuizGame.finish()` : montre les résultats et les enregistre.

**Les autres petits fichiers**

- `timed_input.py` : `timed_input(prompt, deadline)` lit la réponse avant la fin du temps.
  `render(buf)` est une petite fonction à l'intérieur qui rafraîchit le compte à rebours.
- `settings.py` : `BASE_DIR` indique où se trouve le projet ; `LETTERS` contient A, B, C et
  D pour nommer les réponses.
- `quiz.py` : `main()` prépare le jeu console et propose de rejouer. Ce fichier partage
  aussi les noms des classes avec `app.py` pour que les anciens imports continuent de
  marcher.

**Les écrans dans `app.py`**

- `md_escape(text)` : protège le texte pour qu'il s'affiche correctement dans la page.
- `nbsp_punct(text)` : empêche un signe comme `?` de se retrouver tout seul sur une ligne.
- `game()` : retrouve la partie en cours.
- `current_player(g)` : retrouve le joueur qui doit répondre.
- `start_game(names, category, seconds, per_player)` : prépare une nouvelle partie.
- `on_next()` : passe à la question suivante ou affiche les résultats.
- `on_restart()` : prépare une nouvelle partie.
- `timer_bar(remaining, total)` : dessine la barre du temps.
- `timer_fragment()` : regarde le temps chaque seconde et arrête la question à zéro.
- `setup_view()` : montre le formulaire de départ.
- `game_view()` : montre la question et les boutons de réponse.
- `results_view()` : montre les gagnants et le bouton pour rejouer.
- Le routeur à la fin de `app.py` choisit quel écran montrer : départ, jeu ou résultats.

**À tester :** démarrer le jeu, jouer jusqu'à zéro, répondre, passer une question et
rejouer.

## 4. Le chemin d'une question

```text
1. Le jeu choisit une catégorie
             │
             v
2. QuestionBank prend une carte
             │
             v
3. Le jeu montre la carte au joueur
             │
             v
4. Le chronomètre commence
             │
       ┌─────┴──────┐
       v            v
   Bonne réponse   Mauvaise réponse
       │            │
       v            v
   Des points      Zéro point
       └─────┬──────┘
             v
5. Le jeu passe au joueur suivant
             │
             v
6. Leaderboard garde les scores
```

## 5. Comment les deux façons de jouer se partagent le travail ?

```text
                    mêmes classes
              ┌──────────┴──────────┐
              v                     v
       ┌─────────────┐       ┌─────────────┐
       │  quiz.py    │       │   app.py    │
       │ terminal    │       │ page web    │
       └──────┬──────┘       └──────┬──────┘
              └──────────┬──────────┘
                         v
       Questions + joueurs + jokers + scores
```

Les interfaces sont différentes, comme deux télécommandes différentes pour le même jeu.
Les règles et les classes sont partagées.

## 6. Conseils faciles pour l'équipe

- Chacun commence par les fichiers de sa partie.
- Avant de changer le nom ou les entrées d'une méthode, prévenir les deux autres.
- Si une personne change les données d'une question, vérifier que les deux interfaces
  fonctionnent encore.
- Garder `leaderboard.json` à l'abri pendant les essais, car une partie peut le modifier.
- Faire de petits changements et sauvegarder souvent avec Git.
- Quand un fichier change, demander : « Est-ce que le jeu démarre encore ? Est-ce que je
  peux répondre ? Est-ce que le score est bon ? »

## 7. Comment démarrer le jeu ?

Dans le terminal, se placer dans le dossier du projet.

Pour le jeu dans le terminal :

```bash
python3 quiz.py
```

Pour le jeu dans le navigateur :

```bash
pip install -r requirements.txt
streamlit run app.py
```

Pour vérifier que Python comprend les fichiers :

```bash
python3 -m py_compile quiz.py settings.py timed_input.py question.py question_bank.py question_context.py joker.py player.py leaderboard.py quiz_game.py app.py
```
