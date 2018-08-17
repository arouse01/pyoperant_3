import socket

# added pyoperant prefix to module names 1/17/18 AR
hostname = socket.gethostname()

if 'vogel' in hostname:
    from pyoperant.local_vogel import *
elif 'zog' in hostname:
    from pyoperant.local_zog import *
elif 'Aperture' in hostname:
    from pyoperant.local_rouse import *
