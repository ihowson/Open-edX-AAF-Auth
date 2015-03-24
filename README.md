# Open-edX-AAF-Auth

Australian Access Federation authentication for Open edX.

# Status

The auth part ought to work well - I haven't had any complaints. The integration with Open edX is messy and requires some fiddling. See below for more information.

# Design

Third-party auth for Open edX works like:

* You authenticate against the third-party auth provider (e.g. Google, Facebook, Twitter)
* Open edX creates a new user account for you and links that account to the third-party auth provider
* You then (roughly) perform the signup process from scratch
* In future, you authenticate against the third-party provider instead of Open edX. This saves you from having to remember another password.

I wanted a completely integrated auth solution, so accounts that existed at my institution's directory were immediately usable *without* a 'create an Open edX account' step. So, the workflow is:

* You arrive at the Open edX site
* You authenticate against AAF
* Open edX pulls relevant information out of AAF and you immediately start using it

# Setup

* Clone this repo into `edx-platform/common/djangoapps/aaf_auth`
* Enable it in your `lms.env.conf` and `cms.env.conf`

# The nasty part

There are lots of URLs in Open edX that involve user and password management. They all go away now, as it doesn't make sense to change things like usernames and passwords when they're actually managed on an external server. 

I've taken the step of *disabling these URLs entirely*. Note that commenting them out of `urls.py` isn't a great idea, as they're used all over the place in templates. Instead, I've stuck a 'return' into the view handlers for them.

Users still have links all over the place for actions like 'create an account' and 'change your password'. I stripped them out of the template. This is annoying and heavy-handed, but I didn't see a better option at the time. 

# TODO

* Docs!
* Discussion boards show usernames, not human names. This isn't very nice to look at.
* Installation is rubbish.
* I haven't tested on any of the named releases (Aspen/Birch/future release) yet.

Get in contact if you want a hand with integration.

