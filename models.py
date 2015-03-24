from django.db import models


class JTILog(models.Model):
    '''
    Stores previously used JTI claims. If we receive a JTI from a JWT that
    is already in this list, we should not reuse it.
    '''
    # NOTE: 64 is a guess based on what is coming back from AAF. Spec doesn't
    # seem to specify limits.
    jti = models.CharField(max_length=64)
