# MariTrust — socle technique (semaine 2)

## Lancer le projet
```bash
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # comptes, ports, 12 critères
python manage.py runserver      # http://127.0.0.1:8000
```

Comptes de démo (mot de passe : `demo1234`) : `declarant1`, `agent1`, `admin1`.
Interface d'administration Django : `/django-admin/` (compte `admin1`).

## Base de données
Par défaut SQLite (rien à installer). Pour PostgreSQL, définir avant de lancer :
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

## Temps réel
Sans Redis, Channels utilise une couche en mémoire (suffisant pour développer).
Avec Redis : définir `REDIS_URL=redis://localhost:6379`.

## Structure
- `accounts` : utilisateurs, rôles, société de rattachement
- `declarations` : navires, opérateurs, ports, déclarations, historique
- `scoring` : critères et détail du score
- `dashboard` : espaces déclarant / agent / admin
- `templates/` : base Bootstrap, connexion, pages d'espace
