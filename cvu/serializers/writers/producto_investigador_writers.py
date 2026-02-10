from rest_framework import serializers

from cvu.constants import POSSIBLE_TITLE_ATTRS
from cvu.models import ProductoInvestigador
from cvu.utils import search_in_dict


class ProductoInvestigadorRegisterSerializer(serializers.ModelSerializer):
    # Make eje and titulo writable so we can accept them or compute them from `contenido`
    eje = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=128
    )
    titulo = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=512
    )

    class Meta:
        model = ProductoInvestigador
        fields = ["eje", "titulo", "contenido", "tipo", "investigador", "is_from_file"]
        extra_kwargs = {
            # No marcar como `required` aquí: los derivamos desde `contenido` cuando faltan
            "eje": {"required": False, "allow_null": True, "max_length": 128},
            "titulo": {"required": False, "allow_null": True, "max_length": 512},
            "contenido": {"required": True, "allow_null": False},
            "tipo": {"required": True, "allow_null": False},
            "investigador": {"required": True, "allow_null": False},
            "is_from_file": {"required": False, "default": False},
        }

    def _derive_eje_and_titulo(self, contenido):
        """Helper para extraer `eje` y `titulo` del campo `contenido` (si es dict).

        Devuelve tupla (eje, titulo). Valores vacíos si no se encuentran.
        """
        eje = ""
        titulo = ""
        if not contenido:
            return eje, titulo

        # Si contenido es JSON serializado en string, intentar convertirlo
        if isinstance(contenido, str):
            try:
                import json

                contenido = json.loads(contenido)
            except ValueError:
                return eje, titulo

        if isinstance(contenido, dict):
            eje = contenido.get("eje", "") or ""
            titulo = search_in_dict(contenido, POSSIBLE_TITLE_ATTRS) or ""

        return eje, titulo

    def create(self, validated_data):
        # Derivar eje y titulo desde `contenido` si no vienen proporcionados
        contenido = validated_data.get("contenido")
        eje = validated_data.get("eje")
        titulo = validated_data.get("titulo")

        derived_eje, derived_titulo = self._derive_eje_and_titulo(contenido)

        if not eje and derived_eje:
            validated_data["eje"] = derived_eje
        if not titulo and derived_titulo:
            validated_data["titulo"] = derived_titulo

        # Crear la instancia usando el modelo
        return ProductoInvestigador.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Permitir recalcular eje/titulo al actualizar si no vienen
        contenido = validated_data.get("contenido", instance.contenido)
        eje = validated_data.get("eje")
        titulo = validated_data.get("titulo")

        derived_eje, derived_titulo = self._derive_eje_and_titulo(contenido)

        if not eje and derived_eje:
            validated_data["eje"] = derived_eje
        if not titulo and derived_titulo:
            validated_data["titulo"] = derived_titulo

        # Actualizar campos en la instancia
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate(self, attrs):
        """Asegurarse de derivar `eje`/`titulo` desde `contenido` antes de la validación final.

        - Si `titulo` no puede derivarse, lanzar ValidationError porque el modelo requiere un título no vacío.
        - Si `eje` puede derivarse y no viene, lo asignamos.
        """
        contenido = attrs.get("contenido")
        eje = attrs.get("eje")
        titulo = attrs.get("titulo")

        derived_eje, derived_titulo = self._derive_eje_and_titulo(contenido)

        if not eje and derived_eje:
            attrs["eje"] = derived_eje
        if not titulo and derived_titulo:
            attrs["titulo"] = derived_titulo

        # título es requerido por el modelo (blank=False). Si todavía no hay título, error.
        if not attrs.get("titulo"):
            raise serializers.ValidationError(
                {
                    "titulo": "No se pudo derivar `titulo` desde `contenido`. Proporcione `titulo`."
                }
            )

        return attrs
