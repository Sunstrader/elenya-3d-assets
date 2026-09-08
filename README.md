# Elenya 3D Assets

Dépôt public des personnages 3D animés d’Elenya.

## Format de livraison

- Modèles web : `characters/<id>/<id>.glb`
- Sources : `sources/<id>/`
- Textures : intégrées au GLB ou dans `characters/<id>/textures/`
- Aperçus : `previews/<id>.webp`
- Taille recommandée : moins de 8 Mo par personnage
- Compression : Draco/Meshopt + textures WebP/KTX2

## Animations minimales

Chaque GLB doit contenir les clips suivants :

- `Idle`
- `Talk`
- `Blink`
- `React`

## Règles d’affichage

Le fond du jeu reste fixe. Le personnage est rendu sur une couche transparente,
ancré en bas et limité à une hauteur visuelle d’environ 72 % sur ordinateur et
58 % sur mobile. Le cadrage est défini dans `characters.json`.

Les sprites 2D existants restent le mode de secours tant qu’un modèle 3D validé
n’est pas disponible.
