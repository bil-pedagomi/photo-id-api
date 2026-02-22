# Photo ID API — Pedagomi

Micro-service qui retire l'arrière-plan ET recadre automatiquement une photo sur le visage au format photo d'identité (35x45mm).

## Comment ça marche

Tu envoies l'URL d'une photo → le service te renvoie une photo d'identité propre (fond blanc, visage centré, bonne taille).

```
POST /process
{
    "image_url": "https://example.com/photo.jpg"
}
→ Retourne l'image traitée (JPEG)
```

## Déploiement sur Render (gratuit)

### Étape 1 : Crée un compte GitHub
- Va sur github.com et crée un compte si t'en as pas

### Étape 2 : Crée un nouveau repository
- Clique "New repository"
- Nom : `photo-id-api`
- Mets-le en "Public"
- Upload les 4 fichiers : `app.py`, `requirements.txt`, `Dockerfile`, `render.yaml`

### Étape 3 : Déploie sur Render
- Va sur render.com et crée un compte gratuit
- Clique "New" → "Web Service"
- Connecte ton GitHub → sélectionne le repo `photo-id-api`
- Render détecte automatiquement le Dockerfile
- Plan : "Free"
- Clique "Create Web Service"
- Attends 5-10 minutes que ça se déploie

### Étape 4 : Récupère ton URL
- Une fois déployé, Render te donne une URL genre :
  `https://photo-id-api-xxxx.onrender.com`
- Teste avec : `https://photo-id-api-xxxx.onrender.com/health`
  → doit répondre `{"status": "ok"}`

## Configuration dans Zapier

### Step 3 : Remplace Remove.bg par "Webhooks by Zapier"

1. App : **Webhooks by Zapier**
2. Event : **POST**
3. URL : `https://photo-id-api-xxxx.onrender.com/process` (ton URL Render)
4. Payload Type : **json**
5. Data :
   - `image_url` : sélectionne le champ **Photo** du Step 1 (Notion)
6. Teste → tu devrais recevoir l'image traitée

### Step 4 : Upload dans Notion
- App : Notion
- Event : Update Database Item
- Champ "Photo 2" : le fichier output du Step 3

## Options avancées

Tu peux personnaliser la requête :

```json
{
    "image_url": "https://...",
    "width": 413,
    "height": 531,
    "bg_color": "white"
}
```

- `width`/`height` : taille en pixels (défaut : 413x531 = 35x45mm à 300dpi)
- `bg_color` : "white" (défaut) ou "transparent"

## Limites du plan gratuit Render

- Le service s'endort après 15 min d'inactivité
- Premier appel après inactivité : ~30-60 secondes de démarrage
- Pour ton usage (~50 photos/mois) c'est largement suffisant
