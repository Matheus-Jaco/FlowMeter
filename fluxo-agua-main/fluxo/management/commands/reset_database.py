from django.core.management.base import BaseCommand
from django.db import transaction
from fluxo.models import FluxoAgua, Sensor, ConsumoDiario


class Command(BaseCommand):
    help = 'Reseta completamente o banco de dados, removendo todos os dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a operação sem pedir confirmação interativa',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            confirm = input(
                'ATENÇÃO: Esta operação irá DELETAR TODOS OS DADOS do banco!\n'
                'Tem certeza que deseja continuar? (digite "RESET" para confirmar): '
            )
            if confirm != 'RESET':
                self.stdout.write(
                    self.style.ERROR('Operação cancelada pelo usuário.')
                )
                return

        try:
            with transaction.atomic():
                # Deleta todos os registros na ordem correta (respeitando foreign keys)
                deleted_fluxo = FluxoAgua.objects.all().count()
                deleted_consumo = ConsumoDiario.objects.all().count()
                deleted_sensor = Sensor.objects.all().count()

                FluxoAgua.objects.all().delete()
                ConsumoDiario.objects.all().delete()
                Sensor.objects.all().delete()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Banco resetado com sucesso!\n'
                        f'   - {deleted_fluxo} registros de FluxoAgua deletados\n'
                        f'   - {deleted_consumo} registros de ConsumoDiario deletados\n'
                        f'   - {deleted_sensor} registros de Sensor deletados'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao resetar banco: {str(e)}')
            )