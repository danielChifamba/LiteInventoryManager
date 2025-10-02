from settings.models import License
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages

def check_license(get_response):
    def middleware(request):
        try:
            license_obj = License.objects.latest('created_at')
        except License.DoesNotExist:
            return redirect('settings:license_page')

        if not license_obj.is_active():
            messages.error(request, 'Your license is expired.')
            return redirect('license_page')

        response = get_response(request)
        return response
    
    return middleware