from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from .models import FluxoAgua, ConsumoDiario, Sensor, MetaConsumo, ControleFluxo, EmailNotification

class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = "__all__"

class FluxoAguaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FluxoAgua
        fields = "__all__"

    def validate_valor(self, value):
        """Aceita strings e converte para Decimal"""
        if isinstance(value, str):
            try:
                # Remove espaços em branco e converte vírgulas para pontos
                value = value.strip().replace(',', '.')
                return Decimal(value)
            except (InvalidOperation, ValueError):
                raise serializers.ValidationError(
                    "Valor deve ser um número válido. Exemplo: '123.45' ou '123,45'"
                )
        return value

class ConsumoDiarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumoDiario
        fields = "__all__"

    def validate_consumo_total(self, value):
        """Aceita strings e converte para Decimal"""
        if isinstance(value, str):
            try:
                # Remove espaços em branco e converte vírgulas para pontos
                value = value.strip().replace(',', '.')
                return Decimal(value)
            except (InvalidOperation, ValueError):
                raise serializers.ValidationError(
                    "Consumo total deve ser um número válido. Exemplo: '123.45' ou '123,45'"
                )
        return value


class MetaConsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaConsumo
        fields = "__all__"


class ControleFluxoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControleFluxo
        fields = ['data', 'status', 'desligamento_automatico_ocorreu', 'usuario_alterou_manualmente', 'email_enviado_hoje', 'data_hora_atualizacao']
        read_only_fields = ['data', 'desligamento_automatico_ocorreu', 'email_enviado_hoje', 'data_hora_atualizacao']


class EmailNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailNotification
        fields = ['id', 'email', 'ativo', 'data_criacao', 'data_atualizacao']
        read_only_fields = ['id', 'data_criacao', 'data_atualizacao']

    def validate_email(self, value):
        """Valida formato do email"""
        if not value:
            raise serializers.ValidationError("Email é obrigatório")
        return value.lower().strip()
