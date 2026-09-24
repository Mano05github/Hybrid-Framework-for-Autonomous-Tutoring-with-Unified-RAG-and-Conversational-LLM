from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Smoke test the configured CHANNEL_LAYERS backend by send/receive round trip.'

    def handle(self, *args, **options):
        layer = get_channel_layer()
        if layer is None:
            raise CommandError('No channel layer configured.')

        backend = settings.CHANNEL_LAYERS.get('default', {}).get('BACKEND', 'unknown')
        self.stdout.write(f'Channel backend: {backend}')

        try:
            channel_name = async_to_sync(layer.new_channel)('smoke.test.')
            payload = {
                'type': 'smoke.test',
                'value': 'ok',
            }
            async_to_sync(layer.send)(channel_name, payload)
            received = async_to_sync(layer.receive)(channel_name)

            if received.get('type') != 'smoke.test' or received.get('value') != 'ok':
                raise CommandError(f'Unexpected payload from channel layer: {received}')

            self.stdout.write(self.style.SUCCESS('Channel layer smoke test passed.'))
        except Exception as exc:
            raise CommandError(f'Channel layer smoke test failed: {exc}')
