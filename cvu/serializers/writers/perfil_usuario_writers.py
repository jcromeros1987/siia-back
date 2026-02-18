from rest_framework import serializers
from cvu.models import PerfilUsuario


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para lectura de PerfilUsuario."""

    usuario_id = serializers.SerializerMethodField()
    fotografia = serializers.SerializerMethodField()

    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "usuario_id",
            "cvu",
            "nivel_academico",
            "titulo",
            "fotografia",
            "semblanza",
            "linkedin",
            "orcid",
            "correo_alternativo",
            "curp",
            "rfc",
            "fecha_nacimiento",
            "intereses",
            "habilidades",
            "sexo",
            "pais_nacimiento",
            "entidad_federativa",
            "estado_civil",
            "nacionalidad",
            "area_conocimiento",
            "fecha_creacion",
            "fecha_modificacion",
        ]
        read_only_fields = ["id", "fecha_creacion", "fecha_modificacion"]

    def get_usuario_id(self, obj):
        return str(obj.usuario.id)

    def get_fotografia(self, obj):
        if obj.fotografia_uri:
            return {
                "nombre": obj.fotografia_nombre,
                "contentType": obj.fotografia_content_type,
                "uri": obj.fotografia_uri,
            }
        return None


class PerfilUsuarioRegisterSerializer(serializers.ModelSerializer):
    """Serializer para creación/actualización de PerfilUsuario."""

    fotografia = serializers.DictField(required=False, allow_null=True)

    class Meta:
        model = PerfilUsuario
        fields = [
            "usuario",
            "cvu",
            "nivel_academico",
            "titulo",
            "fotografia",
            "semblanza",
            "linkedin",
            "orcid",
            "correo_alternativo",
            "curp",
            "rfc",
            "fecha_nacimiento",
            "intereses",
            "habilidades",
            "sexo",
            "pais_nacimiento",
            "entidad_federativa",
            "estado_civil",
            "nacionalidad",
            "area_conocimiento",
        ]
        extra_kwargs = {
            "usuario": {"required": True},
            "cvu": {"required": False, "allow_null": True},
            "nivel_academico": {"required": False, "allow_null": True},
            "titulo": {"required": False, "allow_null": True},
            "semblanza": {"required": False, "allow_null": True},
            "linkedin": {"required": False, "allow_null": True},
            "orcid": {"required": False, "allow_null": True},
            "correo_alternativo": {"required": False, "allow_null": True},
            "curp": {"required": False, "allow_null": True},
            "rfc": {"required": False, "allow_null": True},
            "fecha_nacimiento": {"required": False, "allow_null": True},
            "intereses": {"required": False, "allow_null": True},
            "habilidades": {"required": False, "allow_null": True},
            "sexo": {"required": False, "allow_null": True},
            "pais_nacimiento": {"required": False, "allow_null": True},
            "entidad_federativa": {"required": False, "allow_null": True},
            "estado_civil": {"required": False, "allow_null": True},
            "nacionalidad": {"required": False, "allow_null": True},
            "area_conocimiento": {"required": False, "allow_null": True},
        }

    def create(self, validated_data):
        fotografia = validated_data.pop("fotografia", None)

        perfil = PerfilUsuario.objects.create(**validated_data)

        if fotografia:
            perfil.fotografia_nombre = fotografia.get("nombre")
            perfil.fotografia_content_type = fotografia.get("contentType")
            perfil.fotografia_uri = fotografia.get("uri")
            perfil.save()

        return perfil

    def update(self, instance, validated_data):
        fotografia = validated_data.pop("fotografia", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if fotografia is not None:
            instance.fotografia_nombre = fotografia.get("nombre")
            instance.fotografia_content_type = fotografia.get("contentType")
            instance.fotografia_uri = fotografia.get("uri")

        instance.save()
        return instance
