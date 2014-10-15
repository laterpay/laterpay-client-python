from django.conf import settings
from django.http import HttpResponseRedirect
from laterpay.django import get_laterpay_client


LPTOKEN_COOKIENAME = getattr(settings, 'LPTOKEN_COOKIENAME', '__lptoken')


class LPTokenMiddleware(object):

    exempt_paths = []

    @classmethod
    def add_exempt_paths(cls, *paths):
        """
        Exempts given ``paths`` from processing by ``LPTokenMiddleware``.
        """
        cls.exempt_paths.extend(paths)

    def process_request(self, request):
        """
        Pulls the LPToken out of our cookie if we have set
        it, and adds it to the request object for easy access
        during views.
        """
        if request.path in self.exempt_paths:
            return

        lptoken = request.GET.get('lptoken', None)

        if lptoken is None:
            if LPTOKEN_COOKIENAME in request.COOKIES:
                # we have a token already, carry on
                lptoken = request.COOKIES[LPTOKEN_COOKIENAME]
            else:
                # we don't have a cookie, so we need to go to /identify to get one
                # first figure out where we are, so we can get back
                if request.method == 'GET':
                    here = request.build_absolute_uri()
                    return HttpResponseRedirect(
                        get_laterpay_client(None).get_gettoken_redirect(return_to=here)
                    )
                else:
                    # for now, just carry on without a token
                    pass

        request.laterpay = get_laterpay_client(lptoken)

    def process_response(self, request, response):
        """
        If the LPToken has been added to the request
        object, set the cookie on the response to ensure
        we get it next request.
        """
        if not hasattr(request, 'laterpay'):
            # this means that some other middleware returned from process_request
            # before ours was run - for example, the django middleware which adds
            # a trailing slash to URLs will do this
            return response

        if request.laterpay.lptoken:
            response.set_cookie(LPTOKEN_COOKIENAME, request.laterpay.lptoken)
        else:
            response.delete_cookie(LPTOKEN_COOKIENAME)
            here = request.build_absolute_uri()
            return HttpResponseRedirect(
                request.laterpay.get_gettoken_redirect(return_to=here)
            )
        return response
