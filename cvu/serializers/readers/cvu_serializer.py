from rest_framework import serializers

from cvu.constants import POSSIBLE_TITLE_ATTRS
from cvu.utils import search_in_dict


class ProductoSerializer(serializers.Serializer):
    id = serializers.CharField()
    eje = serializers.CharField(required=False, allow_null=True)
    titulo = serializers.SerializerMethodField()
    contenido = serializers.SerializerMethodField()

    def get_titulo(self, obj):
        titulo = search_in_dict(obj, POSSIBLE_TITLE_ATTRS)
        return titulo

    def get_contenido(self, obj):
        return obj


class ProductoInvestigadorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    id_producto = serializers.CharField()
    eje = serializers.CharField(required=False, allow_null=True)
    titulo = serializers.CharField(required=False, allow_null=True)
    contenido = serializers.DictField(required=False, allow_null=True)
    is_from_file = serializers.BooleanField()


class AportacionesSerializer(serializers.Serializer):
    articulosCientifica = ProductoSerializer(many=True, required=False)
    librosCientifica = ProductoSerializer(many=True, required=False)
    capitulosCientifica = ProductoSerializer(many=True, required=False)
    articulosDifusion = ProductoSerializer(many=True, required=False)
    librosDifusion = ProductoSerializer(many=True, required=False)
    capitulosDifusion = ProductoSerializer(many=True, required=False)
    desarrolloTecnologicoInnovacion = ProductoSerializer(many=True, required=False)
    propiedadIntelectual = ProductoSerializer(many=True, required=False)
    transferenciaTecnologica = ProductoSerializer(many=True, required=False)


class FotografiaSerializer(serializers.Serializer):
    nombre = serializers.CharField(required=False, allow_null=True)
    contentType = serializers.CharField(required=False, allow_null=True)
    uri = serializers.CharField(required=False, allow_null=True)


class AreaItemSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    nombre = serializers.CharField(required=False, allow_null=True)
    clave = serializers.CharField(required=False, allow_null=True)
    version = serializers.CharField(required=False, allow_null=True)


class CampoDisciplinaSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    nombre = serializers.CharField(required=False, allow_null=True)
    clave = serializers.CharField(required=False, allow_null=True)


class AreaConocimientoSerializer(serializers.Serializer):
    area = AreaItemSerializer(required=False, allow_null=True)
    campo = CampoDisciplinaSerializer(required=False, allow_null=True)
    disciplina = CampoDisciplinaSerializer(required=False, allow_null=True)
    subdisciplina = CampoDisciplinaSerializer(required=False, allow_null=True)


class IdNombreSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    nombre = serializers.CharField(required=False, allow_null=True)


class PrincipalSerializer(serializers.Serializer):
    fotografia = FotografiaSerializer(required=False, allow_null=True)
    semblanza = serializers.CharField(required=False, allow_null=True)
    linkedin = serializers.CharField(required=False, allow_null=True)
    intereses = serializers.ListField(child=serializers.CharField(), required=False)
    habilidades = serializers.ListField(child=serializers.CharField(), required=False)
    orcId = serializers.CharField(required=False, allow_null=True)
    curp = serializers.CharField(required=False, allow_null=True)
    nombre = serializers.CharField(required=False, allow_null=True)
    primerApellido = serializers.CharField(required=False, allow_null=True)
    segundoApellido = serializers.CharField(required=False, allow_null=True)
    fechaNacimiento = serializers.CharField(required=False, allow_null=True)
    sexo = IdNombreSerializer(required=False, allow_null=True)
    paisNacimiento = IdNombreSerializer(required=False, allow_null=True)
    entidadFederativa = serializers.DictField(required=False, allow_null=True)
    rfc = serializers.CharField(required=False, allow_null=True)
    estadoCivil = IdNombreSerializer(required=False, allow_null=True)
    nacionalidad = IdNombreSerializer(required=False, allow_null=True)
    areaConocimiento = AreaConocimientoSerializer(required=False, allow_null=True)


class FormacionContinuaSerializer(serializers.Serializer):
    cursos = ProductoSerializer(many=True, required=False)
    certificacionesMedicas = ProductoSerializer(many=True, required=False)


class IdiomaLenguaSerializer(serializers.Serializer):
    idiomas = ProductoSerializer(many=True, required=False)
    lenguas = ProductoSerializer(many=True, required=False)


class PerfilSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    cvu = serializers.CharField(required=False, allow_null=True)
    login = serializers.CharField(required=False, allow_null=True)
    correoAlternativo = serializers.CharField(required=False, allow_null=True)
    nivelAcademico = serializers.CharField(required=False, allow_null=True)
    titulo = serializers.CharField(required=False, allow_null=True)
    principal = PrincipalSerializer(required=False, allow_null=True)
    trayectoriaAcademica = ProductoSerializer(many=True, required=False)
    formacionContinua = FormacionContinuaSerializer(required=False)
    logros = ProductoSerializer(many=True, required=False)
    idiomaLengua = IdiomaLenguaSerializer(required=False, allow_null=True)
    trayectoriaProfesional = ProductoSerializer(many=True, required=False)
    evaluacionesOtorgadas = ProductoSerializer(many=True, required=False)
    estancias = ProductoSerializer(many=True, required=False)
    cursosImpartidos = ProductoSerializer(many=True, required=False)
    congresos = ProductoSerializer(many=True, required=False)
    createdDate = serializers.DateTimeField(required=False, allow_null=True)
    lastModifiedDate = serializers.DateTimeField(required=False, allow_null=True)


class IdentificadorInstitucionSerializer(serializers.Serializer):
    nombre = serializers.CharField(required=False, allow_null=True)
    valor = serializers.CharField(required=False, allow_null=True)


class PerfilCompletoSerializer(serializers.Serializer):
    aportaciones = AportacionesSerializer(required=False)
    perfil = PerfilSerializer(required=False)
    filtro = serializers.CharField(required=False, allow_null=True)
    nombreInstituciónReceptora = serializers.CharField(required=False, allow_null=True)
    identificadorInstitucion = IdentificadorInstitucionSerializer(required=False)
