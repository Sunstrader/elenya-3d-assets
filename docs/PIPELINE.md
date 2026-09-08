# Pipeline de production

1. Créer ou convertir le personnage en modèle humanoïde riggé.
2. Conserver la ressemblance avec le sprite 2D de référence.
3. Ajouter les clips `Idle`, `Talk`, `Blink` et `React`.
4. Exporter en GLB avec textures incorporées.
5. Optimiser le GLB pour le Web, cible inférieure à 8 Mo.
6. Placer le fichier dans `characters/<id>/<id>.glb`.
7. Ajouter un aperçu transparent dans `previews/<id>.webp`.
8. Régler le cadrage dans `characters.json`, puis passer `enabled` à `true`.

## Contrôle visuel

- Aucun étirement de l’image.
- Pieds proches du bas de l’écran.
- Visage visible sans masquer les choix.
- Fond du jeu immobile.
- Animation discrète : respiration, clignement, petit mouvement de tête.
- Mode 2D automatique si WebGL ou le modèle échoue.
