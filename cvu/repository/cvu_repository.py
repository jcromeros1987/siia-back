# ========================================================
# VALIDAR DATOS PERSONALES DEL CVU
# ========================================================

def validate_cvu_datos_personales(
    self,
    investigador_id: UUID,
    cvu_usuario_id: str,
    nombre: str,
    primer_apellido: str = None,
    segundo_apellido: str = None
) -> Result[bool]:
    """
    Valida el nombre del archivo CVU contra el nombre
    registrado en el perfil existente del usuario.

    Esta etapa corresponde a SUB-CK-014.2.

    Flujo:

        1. Se utiliza investigador_id para identificar
           al usuario que está realizando la carga.

        2. Se utiliza cvu_usuario_id para identificar
           exactamente el perfil CVU que ya fue validado.

        3. Se obtiene el nombre registrado en BD.

        4. Se compara contra el nombre recibido desde
           perfil.principal.nombre del JSON.

        5. Si coinciden:
               permite continuar.

        6. Si NO coinciden:
               rechaza la carga.

    IMPORTANTE:

        En SUB-CK-014.2 solamente se valida el nombre.

        Los parámetros primer_apellido y segundo_apellido
        se reciben porque CVUService ya los proporciona,
        pero todavía NO participan en la validación.

    No se realiza ningún UPDATE ni INSERT en este método.
    """

    # ----------------------------------------------------
    # BUSCAR PERFIL EXISTENTE
    # ----------------------------------------------------
    #
    # El usuario_id del CVU ya fue validado previamente
    # mediante validate_cvu_usuario_id().
    #
    # Aun así, utilizamos ambos identificadores para evitar
    # validar el nombre contra un perfil diferente.

    perfil = (
        PerfilUsuario.objects
        .filter(
            usuario=investigador_id,
            usuario_id=cvu_usuario_id
        )
        .first()
    )

    # ----------------------------------------------------
    # VALIDAR EXISTENCIA DEL PERFIL
    # ----------------------------------------------------

    if not perfil:

        return Result.err_from(
            ErrorCode.VALIDATION_ERROR,
            "No se encontró el perfil del usuario para validar el nombre."
        )

    # ----------------------------------------------------
    # VALIDAR QUE EL JSON CONTENGA NOMBRE
    # ----------------------------------------------------

    nombre_cvu = (
        str(nombre).strip().casefold()
        if nombre is not None
        else ""
    )

    if not nombre_cvu:

        return Result.err_from(
            ErrorCode.VALIDATION_ERROR,
            "El archivo CVU no contiene el nombre requerido para la validación."
        )

    # ----------------------------------------------------
    # OBTENER Y NORMALIZAR NOMBRE DE BD
    # ----------------------------------------------------

    nombre_bd = (
        str(perfil.nombre).strip().casefold()
        if perfil.nombre is not None
        else ""
    )

    # ----------------------------------------------------
    # VALIDAR QUE BD TENGA NOMBRE
    # ----------------------------------------------------

    if not nombre_bd:

        return Result.err_from(
            ErrorCode.VALIDATION_ERROR,
            "El perfil registrado no contiene un nombre para realizar la validación."
        )

    # ----------------------------------------------------
    # COMPARAR NOMBRE CVU CONTRA NOMBRE BD
    # ----------------------------------------------------

    if nombre_cvu != nombre_bd:

        logger.warning(
            "Carga de CVU rechazada por diferencia de nombre. "
            "investigador_id=%s, cvu_usuario_id=%s, "
            "nombre_cvu=%s, nombre_bd=%s",
            investigador_id,
            cvu_usuario_id,
            nombre,
            perfil.nombre,
        )

        return Result.err_from(
            ErrorCode.VALIDATION_ERROR,
            "No se puede cargar el CVU porque el nombre del archivo "
            "no coincide con el nombre registrado."
        )

    # ----------------------------------------------------
    # VALIDACIÓN CORRECTA
    # ----------------------------------------------------
    #
    # No se modifica ningún dato.
    # Simplemente se permite continuar con el flujo normal
    # de CVUService.

    return Result.ok(True)