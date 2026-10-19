from django.db import migrations, models


def populate_codes(apps, schema_editor):
    """Attribue un code stable à chaque Critere existant selon son nom."""
    Critere = apps.get_model("scoring", "Critere")
    mapping = {
        "Poids incohérent avec le type de conteneur": "poids_conteneur",
        "Marchandise sensible": "marchandise_sensible",
        "Marchandise inhabituelle pour la route": "route_inhabituelle",
        "Valeur déclarée très inférieure au marché": "valeur_sous_evaluee",
        "Escale dans un port à risque (par port)": "port_a_risque",
        "Changement de pavillon récent": "pavillon_recent",
        "Infractions passées du navire (par infraction)": "infractions_navire",
        "Anomalie du signal AIS": "anomalie_ais",
        "Opérateur inconnu": "operateur_inconnu",
        "Déclaration trop proche de l'arrivée": "declaration_tardive",
        "Documents incohérents entre eux": "documents_incoherents",
        "Moyen de paiement atypique": "paiement_atypique",
    }
    to_update = []
    for critere in Critere.objects.all():
        if not critere.code:
            critere.code = mapping.get(critere.nom, "autre")
            to_update.append(critere)
    if to_update:
        Critere.objects.bulk_update(to_update, ["code"])


def reverse_codes(apps, schema_editor):
    """Supprime tous les codes (rollback)."""
    Critere = apps.get_model("scoring", "Critere")
    Critere.objects.update(code=None)


class Migration(migrations.Migration):

    dependencies = [
        ("scoring", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="critere",
            name="code",
            field=models.SlugField(
                blank=True,
                null=True,
                unique=True,
                help_text="Identifiant stable du critère (ex: poids_conteneur).",
            ),
        ),
        migrations.RunPython(populate_codes, reverse_codes),
        migrations.AlterField(
            model_name="critere",
            name="code",
            field=models.SlugField(
                unique=True,
                help_text="Identifiant stable du critère (ex: poids_conteneur).",
            ),
        ),
    ]
