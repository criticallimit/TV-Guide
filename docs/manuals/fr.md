# TV Guide pour Home Assistant


Le Royaume-Uni est également pris en charge avec une liste préparée de chaînes principales.
Consultez le programme TV, préparez votre soirée et enregistrez vos émissions avec des rappels. Le guide s’adapte aux grands écrans et aux téléphones, en mode clair ou sombre.

[Dansk](https://criticallimit.github.io/TV-Guide/manuals/da.html) · [Deutsch](https://criticallimit.github.io/TV-Guide/manuals/de.html) · [English](https://criticallimit.github.io/TV-Guide/manuals/en.html) · [Español](https://criticallimit.github.io/TV-Guide/manuals/es.html) · [Nederlands](https://criticallimit.github.io/TV-Guide/manuals/nl.html) · [Français](https://criticallimit.github.io/TV-Guide/manuals/fr.html) · [Italiano](https://criticallimit.github.io/TV-Guide/manuals/it.html) · [Norsk](https://criticallimit.github.io/TV-Guide/manuals/nb.html) · [Svenska](https://criticallimit.github.io/TV-Guide/manuals/sv.html)

## Installation

Vous avez besoin de Home Assistant avec la boutique d’applications/add-ons, par exemple Home Assistant OS.

1. Ouvrez **Paramètres → Applications** (ou **Modules complémentaires**) puis la boutique.
2. Ajoutez `https://github.com/criticallimit/TV-Guide` dans **Dépôts**.
3. Installez et démarrez **TV Guide**, puis activez son affichage dans la barre latérale.
4. Ouvrez **TV Guide**. Le premier chargement des programmes peut prendre quelques minutes.

## Pays et langue

Ouvrez les paramètres avec le bouton en forme d’engrenage. Dans **Pays et langue**, choisissez l’Allemagne, l’Autriche, la Suisse, les Pays-Bas, la Belgique, le Danemark, la Norvège, la France ou la Suède. Chaque pays dispose de chaînes principales et d’autres chaînes selon les données disponibles. La Suisse inclut ses trois régions linguistiques ; la Belgique inclut des chaînes néerlandophones et francophones.

**Automatique · Home Assistant** utilise d’abord la langue de votre profil, puis les paramètres de l’installation. Sans langue disponible, le guide utilise le danois pour le Danemark, l’allemand pour l’Allemagne et l’Autriche, le néerlandais pour les Pays-Bas, le norvégien pour la Norvège, le français pour la France et le suédois pour la Suède. Pour les pays multilingues, il utilise la langue du navigateur, avec l’anglais comme solution de repli. Vous pouvez aussi choisir le danois, l’allemand, l’anglais, le néerlandais, le français, l’italien, le norvégien ou le suédois. Le pays et la langue sont indépendants. Les titres et descriptions conservent leur langue d’origine.

## Programmes et chaînes

Choisissez **Maintenant**, **18:00**, **20:15**, **22:00** ou **Autres horaires**. Touchez une émission pour ouvrir ses détails. **Chaînes principales** affiche la liste préparée. Utilisez **☰ Chaînes** pour choisir et organiser **Mes chaînes**. Votre sélection est conservée pour chaque pays ; **Ordre par défaut** rétablit la liste initiale.

Les paramètres sont regroupés en **Pays et langue**, **Affichage** et **Rappels**. Réglez la vue initiale, l’apparence et le nombre de chaînes dans Affichage. **0** affiche toute la liste sélectionnée. L’intervalle d’actualisation est dans **Avancé**. Cliquez sur **Enregistrer** pour appliquer les changements.

## Enregistrer et recevoir des rappels

Ouvrez une émission et choisissez **Enregistrer**. Retrouvez-la dans **★ Enregistrés**. Pour une émission à venir enregistrée, activez **Me rappeler**, 5, 10, 15 ou 30 minutes avant.

Dans les paramètres, ouvrez **Rappels**, choisissez Home Assistant ou un appareil mobile connecté et utilisez **Tester la notification**. Home Assistant et TV Guide doivent fonctionner au moment du rappel. Un rappel conserve la langue utilisée lors de sa création.

## Sur votre tableau de bord

Ouvrez **Sur votre tableau de bord** dans les paramètres. Dans Home Assistant, ouvrez **Paramètres → Tableaux de bord → Ressources** et ajoutez `/local/tv-guide-card-loader.js` comme **Module JavaScript**. Activez le mode avancé dans votre profil si Ressources est masqué. Rechargez Home Assistant et ajoutez la carte TV Guide. Si votre première carte n’apparaît pas, redémarrez Home Assistant une fois.

## Si un élément manque

La disponibilité dépend des sources publiques. Les données confirmées des chaînes sont prioritaires ; d’autres sources comblent les lacunes. Les Pays-Bas utilisent actuellement un programme public vérifié. Toutes les chaînes et dates ne sont pas toujours couvertes. Après une mise à jour ou un changement de pays, laissez le chargement se terminer.

Si un rappel manque, vérifiez son destinataire et envoyez une notification de test. Les appareils mobiles doivent être connectés à l’application Home Assistant.

Installez les mises à jour publiées depuis la boutique. Vos listes et émissions enregistrées sont conservées. Les changements sur main peuvent précéder la prochaine version publiée.

[Signaler un problème](https://github.com/criticallimit/TV-Guide/issues) en précisant le pays, la chaîne, la date et l’heure.

La France propose 24 chaînes nationales principales. BFMTV est temporairement exclue.
