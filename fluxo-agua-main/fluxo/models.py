from django.db import models
from django.utils import timezone

class Sensor(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class FluxoAgua(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="leituras")
    data_hora = models.DateTimeField(default=timezone.now)
    valor = models.DecimalField(max_digits=10, decimal_places=2)  # litros instantâneos
    valor_diferenca = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # diferença entre valor atual e anterior

    def __str__(self):
        return f"{self.sensor.nome} - {self.data_hora} - {self.valor} L"

class ConsumoDiario(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="consumos_diarios")
    data = models.DateField()
    consumo_total = models.DecimalField(max_digits=10, decimal_places=2)
    hora = models.TimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sensor", "data"], name="unique_sensor_data")
        ]

    def __str__(self):
        return f"{self.sensor.nome} - {self.data} - {self.consumo_total} L"


class MetaConsumo(models.Model):
    meta_diaria_litros = models.DecimalField(max_digits=10, decimal_places=2)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Meta de Consumo"
        verbose_name_plural = "Metas de Consumo"

    def __str__(self):
        return f"Meta diária: {self.meta_diaria_litros} L"

    def save(self, *args, **kwargs):
        """Garante que apenas um registro de meta exista"""
        if not self.pk and MetaConsumo.objects.exists():
            # Se já existe uma meta e estamos tentando criar outra, atualiza a existente
            raise ValueError("Já existe uma meta cadastrada. Use PUT/PATCH para atualizar.")
        return super().save(*args, **kwargs)

    @classmethod
    def get_meta_atual(cls):
        """Retorna a meta atual ou None se não existir"""
        return cls.objects.first()


class ControleFluxo(models.Model):
    data = models.DateField(unique=True)
    status = models.CharField(max_length=3, choices=[('on', 'Ligado'), ('off', 'Desligado')], default='on')
    desligamento_automatico_ocorreu = models.BooleanField(default=False)
    usuario_alterou_manualmente = models.BooleanField(default=False)
    email_enviado_hoje = models.BooleanField(default=False)
    data_hora_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Controle de Fluxo"
        verbose_name_plural = "Controles de Fluxo"

    def __str__(self):
        return f"{self.data} - Status: {self.status}"


class EmailNotification(models.Model):
    email = models.EmailField(unique=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Email de Notificação"
        verbose_name_plural = "Emails de Notificação"
        ordering = ['-data_criacao']

    def __str__(self):
        status = "Ativo" if self.ativo else "Inativo"
        return f"{self.email} - {status}"

