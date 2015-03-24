from django.conf import settings
import django.contrib.auth as djauth
from django.contrib.auth.models import User
from django.contrib import messages  # FIXME: this probably isn't hooked up to the front page (e.g. if login fails)
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import NoReverseMatch
from django.shortcuts import redirect
from django.utils.translation import get_language
from django.views.decorators.csrf import csrf_exempt

import jwt
import re

from models import JTILog

from lang_pref import LANGUAGE_KEY
from student.models import create_comments_service_user, UserProfile
from user_api.models import UserPreference


# -----------------------------------------------------------------------------
# AAF (Australian Access Federation))
# -----------------------------------------------------------------------------
def login(request, next_page=None, required=False):
    # Bounce user to the AAF login page

    # We have this view as lots of things embed reverse('login') and I don't
    # want to change them all by hand

    return redirect(settings.AAF_URL)




@csrf_exempt
def callback(request, next_page=None, required=False):
    try:
        if request.method != 'POST':
            raise PermissionDenied('0005')

        try:
            # Verifies signature and expiry time
            verified_jwt = jwt.decode(
                request.POST['assertion'],
                key=settings.AAF_SECRET,
                # audience=settings.AAF_AUDIENCE,
                # issuer=settings.AAF_ISSUER)
            )
        except jwt.ExpiredSignature:
            # Security cookie has expired
            raise PermissionDenied('0001')

        # for PyJWT > 0.4.1:
        '''
        except jwt.InvalidAudience:
            # Not for this audience
            raise PermissionDenied('0004')
            '''
        # for older PyJWT:
        if verified_jwt['aud'] != settings.AAF_AUDIENCE or verified_jwt['iss'] != settings.AAF_ISSUER:
            raise PermissionDenied('0004')

        import logging
        logging.warning(verified_jwt)

        # Verify that we haven't seen this jti value before (prevents replay
        # attacks)
        if 'jti' not in verified_jwt.keys():
            raise PermissionDenied('0002')

        jti = verified_jwt['jti']
        if JTILog.objects.filter(jti=jti).exists():
            # looks like replay
            raise PermissionDenied('0003')

        # add jti to the log
        jl = JTILog(jti=jti)
        jl.save()

        attributes = verified_jwt['https://aaf.edu.au/attributes']

        request.session['attributes'] = attributes
        request.session['jwt'] = verified_jwt
        request.session['jws'] = request.POST['assertion']

        assert 'edupersonprincipalname' in attributes.keys(), 'edupersonprincipalname not in attributes'

        # If you want to restrict access to your institution, fill in PRINCIPAL_NAME_RE and uncomment
        # The first group should be the username
        '''
        match = PRINCIPAL_NAME_RE.match(attributes['edupersonprincipalname'])
        if match is None:
            # Principal name not in expected format
            raise PermissionDenied('0006')
        username = match.groups()[0]
        '''
        username = attributes['edupersonprincipalname']  # Remove this if you have a better/shorter username you'd like to use

        email = attributes['edupersonprincipalname']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None)  # non-usable password
            user.save()

            UserPreference.set_preference(user, LANGUAGE_KEY, get_language())

        # blech - we're caching the user's name both in the Django User object
        # and the edX UserProfile object, and we don't really want either.

        # cache some attributes
        # Django shouldn't touch the database if they haven't changed, so no perf issue
        if 'givenname' in attributes.keys():
            user.first_name = attributes['givenname']

        if 'surname' in attributes.keys():
            user.last_name = attributes['surname']

        # This should only be done at user creation time. We do it here
        # because we have some old entries in the database that we'd like to
        # clean up automatically.
        if 'edupersonprincipalname' in attributes.keys():
            user.email = attributes['edupersonprincipalname']

        user.save()

        # Look up the UserProfile and update it
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            # create a new one
            profile = UserProfile(user=user)
            profile.save()

        # update the profile's name
        profile.update_name('%s %s' % (user.first_name, user.last_name))

        create_comments_service_user(user)

        # Temporary workaround: http://stackoverflow.com/a/23771930
        user.backend = 'django.contrib.auth.backends.ModelBackend'

        djauth.login(request, user)

        # done!
        if next_page:
            return redirect(next_page)
        else:
            # If we're in lms, we want to go to dashboard. For cms, go to homepage.
            print 'doing the fallback thing'
            try:
                return redirect('dashboard')
            except NoReverseMatch:
                return redirect('homepage')

    except PermissionDenied as e:
        if 'attributes' in request.session.keys():
            del request.session['attributes']
        djauth.logout(request)

        # messages.add_message(request, messages.ERROR, 'Could not log you in (error %s). Please try again.' % e.message)

        # bounce back to login page
        # TODO you could bounce to a message page if the messages thing above doesn't integrate nicely
        return redirect('dashboard')  # TODO: probably better to send directly to index, but I can't find it
