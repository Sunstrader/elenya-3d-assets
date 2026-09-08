# Silas — référence de modélisation

## Source officielle

- Sprite original : https://cdn.jsdelivr.net/gh/Sunstrader/Releases@main/Sprites%20-%20Silas%20bg/SPRITE_SILAS_DEBOUT_COURBE_SUPPLIANT_202606231802.png

## Vues obligatoires

Le modèle doit être contrôlé sous toutes les faces avant activation :

- face ;
- trois-quarts avant ;
- profil gauche ;
- dos ;
- profil droit ;
- trois-quarts arrière ;
- gros plan neutre du visage.

## Identité et costume à préserver

Cheveux roux courts et ébouriffés, yeux bleu-gris, cape verte à capuche avec
fermoir en laiton, tunique beige usée, pantalon sombre ample, mollets entourés,
bottes brunes, bâton en bois et grande sacoche de marchand en cuir brun.

## Livraison

Le fichier final doit être `characters/silas/silas.glb`, riggé, optimisé pour
le Web et contenir les clips `Idle`, `Talk`, `Blink` et `React`.
Silas reste `enabled: false` dans `characters.json` jusqu’à validation des
vues avant, arrière et latérales.
