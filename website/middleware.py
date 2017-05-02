class SecurityHeaders:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-XSS-Protection'] = '1; mode=block'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Security-Policy'] = 'default-src \'none\'; style-src *.x86sec.com https://fonts.googleapis.com; font-src https://fonts.googleapis.com; img-src *.x86sec.com;'
        response['Referrer-Policy'] = 'origin'
        return response
