# sdl-jstest-py

Python version of sdl2-jstest with some additions.

## Fonctionnalités :

1. **Liste des manettes** (`-l, --list`) : Affiche toutes les manettes détectées avec leurs propriétés
2. **Test interactif** (`-t, --test`) : Interface curses en temps réel montrant l'état des axes, boutons, hats et balls
3. **Événements** (`-e, --event`) : Affiche les événements de la manette en temps réel
4. **Test de vibration** (`-r, --rumble`) : Structure pour tester la vibration (nécessite des bibliothèques supplémentaires)

## Dépendances requises :

Pour utiliser ce programme, vous devez installer :

```bash
pip install pygame
```

Le module `curses` est inclus dans la bibliothèque standard Python sur Linux.

## Différences principales avec l'original :

1. **Pygame au lieu de SDL2** : Utilise pygame qui est une interface Python pour SDL
2. **Arguments** : Utilise `argparse` pour une gestion plus pythonique des arguments
3. **Gestion des erreurs** : Utilise les exceptions Python
4. **Types** : Ajout d'annotations de types pour une meilleure lisibilité
5. **Vibration** : Le support de la vibration nécessite des bibliothèques supplémentaires comme `evdev` sur Linux

## Utilisation :

```bash
# Lister les manettes
python3 sdl2-jstest.py --list

# Tester la manette 0
python3 sdl2-jstest.py --test 0

# Voir les événements de la manette 0
python3 sdl2-jstest.py --event 0
```

Le programme conserve l'affichage ASCII du programme original et fonctionne de manière similaire sous Linux.

## Rumble et Force Feedback

J'ai ajouté un support complet pour la vibration (rumble) avec plusieurs méthodes de fallback. Voici ce qui a été ajouté :

### Nouvelles fonctionnalités de vibration :

#### 1. **Méthode Pygame (SDL 2.0.18+)**
- Utilise la méthode native `joystick.rumble()` si disponible
- Compatible avec les versions récentes de pygame/SDL2

#### 2. **Méthode evdev (recommandée pour Linux)**
- Accès direct aux capacités de force feedback du kernel Linux
- Support des effets `FF_RUMBLE` et `FF_PERIODIC`
- Gestion complète des effets de vibration

#### 3. **Méthode d'accès direct (fallback)**
- Accès basique aux devices `/dev/input/js*`
- Méthode de derniers recours, fonctionnalité limitée

### Installation des dépendances :

Pour un support complet de la vibration, installez :

```bash
pip install evdev
```

### Permissions requises :

Sur Linux, vous pourriez avoir besoin d'ajouter votre utilisateur au groupe `input` :

```bash
sudo usermod -a -G input $USER
```

Puis redémarrez votre session.

### Utilisation :

```bash
# Tester la vibration sur la manette 0
python3 sdl2-jstest.py --rumble 0
```

### Caractéristiques du support de vibration :

1. **Détection automatique** : Le programme détecte automatiquement quelles méthodes sont disponibles
2. **Fallback intelligent** : Essaie plusieurs méthodes dans l'ordre de préférence
3. **Informations détaillées** : Affiche les capacités de force feedback détectées
4. **Gestion d'erreurs** : Messages clairs si la vibration n'est pas supportée
5. **Nettoyage automatique** : Arrête proprement les effets et libère les ressources

Le programme teste maintenant la vibration de manière similaire au programme C original, avec une durée de 3 secondes à pleine intensité. La méthode evdev offre le contrôle le plus précis et est recommandée pour Linux.

## Force Feedback
J'ai ajouté un support complet pour le **force feedback** (retour de force) utilisé principalement par les volants de course. Voici ce qui a été implémenté :

### Nouveaux effets de force feedback supportés :

#### 1. **Effets de condition** (pour volants)
- **SPRING** : Force de centrage (ressort vers le centre)
- **DAMPER** : Amortissement basé sur la vitesse
- **FRICTION** : Simulation de friction/frottement
- **INERTIA** : Simulation de masse/inertie

#### 2. **Effets de force**
- **CONSTANT** : Force constante dans une direction
- **RAMP** : Force qui change graduellement dans le temps

#### 3. **Effets périodiques**
- **SINE** : Oscillations sinusoïdales (vibrations douces)
- **SQUARE** : Oscillations carrées (vibrations saccadées)

#### 4. **Effets tactiles**
- **RUMBLE** : Vibrations (pour manettes et volants compatibles)

### Utilisation :

```bash
# Test complet du force feedback sur le périphérique 0
python3 sdl2-jstest.py --forcefeedback 0

# Test simple de vibration
python3 sdl2-jstest.py --rumble 0
```

### Fonctionnalités avancées :

1. **Détection automatique des capacités** : Le programme détecte quels effets sont supportés par votre volant
2. **Test séquentiel** : Chaque effet est testé pendant 3 secondes avec des paramètres optimisés
3. **Feedback détaillé** : Affichage des capacités détectées et résultats de chaque test
4. **Gestion d'erreurs** : Messages clairs en cas de problème
5. **Nettoyage automatique** : Tous les effets sont proprement arrêtés et supprimés

### Effets typiques pour volants :

- **SPRING** : Simule le retour au centre du volant
- **DAMPER** : Simule la résistance hydraulique
- **FRICTION** : Simule la friction des pneus sur la route
- **CONSTANT** : Force de virage (understeering/oversteering)
- **PERIODIC** : Vibrations moteur ou route rugueuse

Le programme teste maintenant tous les aspects du force feedback, ce qui est particulièrement utile pour calibrer et tester des volants de course professionnels comme ceux de Logitech, Thrustmaster, Fanatec, etc.
