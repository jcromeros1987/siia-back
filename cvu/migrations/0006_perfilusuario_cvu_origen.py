from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cvu", "0005_perfilusuario_nombre_perfilusuario_primer_apellido_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="cvu_origen",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
