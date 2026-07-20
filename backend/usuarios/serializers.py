from rest_framework import serializers

from .models import Usuario


class UsuarioActualSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    sucursal_nombre = serializers.CharField(
        source="sucursal.nombre", read_only=True, allow_null=True
    )
    sucursales_asignadas = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "nombre_completo",
            "email",
            "telefono",
            "rol",
            "sucursal",
            "sucursal_nombre",
            "sucursales_asignadas",
        )

    def get_nombre_completo(self, usuario: Usuario) -> str:
        return usuario.get_full_name().strip() or usuario.username

    def get_sucursales_asignadas(
        self, usuario: Usuario
    ) -> list[dict[str, str]]:
        return list(
            usuario.sucursales_asignadas.values("id", "codigo", "nombre")
        )


class TecnicoListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ("id", "username", "nombre_completo")

    def get_nombre_completo(self, usuario: Usuario) -> str:
        return usuario.get_full_name().strip() or usuario.username


class UsuarioAdminListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    sucursal_nombre = serializers.CharField(
        source="sucursal.nombre", read_only=True, allow_null=True
    )

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "nombre_completo",
            "email",
            "telefono",
            "rol",
            "sucursal",
            "sucursal_nombre",
            "sucursales_asignadas",
            "activo_operativamente",
            "is_active",
        )

    def get_nombre_completo(self, usuario: Usuario) -> str:
        return usuario.get_full_name().strip() or usuario.username


class UsuarioAdminWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "telefono",
            "rol",
            "sucursal",
            "sucursales_asignadas",
            "activo_operativamente",
            "is_active",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        request = self.context["request"]
        actor = request.user
        rol = attrs.get("rol", getattr(self.instance, "rol", None))
        if actor.rol == Usuario.Rol.SUPERVISOR and rol in (
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.SUPERVISOR,
        ):
            raise serializers.ValidationError(
                {"rol": "Un Supervisor no puede administrar este rol."}
            )
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "La contraseña es obligatoria al crear un usuario."}
            )
        if rol == Usuario.Rol.SUCURSAL and not attrs.get(
            "sucursal", getattr(self.instance, "sucursal", None)
        ):
            raise serializers.ValidationError(
                {"sucursal": "Un usuario Sucursal debe tener una sucursal asignada."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        sucursales = validated_data.pop("sucursales_asignadas", [])
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        usuario.sucursales_asignadas.set(sucursales)
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        sucursales = validated_data.pop("sucursales_asignadas", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=("password",))
        if sucursales is not None:
            instance.sucursales_asignadas.set(sucursales)
        if instance.rol != Usuario.Rol.SUCURSAL and instance.sucursal_id:
            instance.sucursal = None
            instance.save(update_fields=("sucursal",))
        if instance.rol != Usuario.Rol.JDISTRITO:
            instance.sucursales_asignadas.clear()
        return instance
