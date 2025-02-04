import logging.handlers

smtp_handler = logging.handlers.SMTPHandler(mailhost="localhost",
                                            toaddrs='andrew.rouse@tufts.edu',
                                            fromaddr='Aperture <aperturefinch@gmail.com>',
                                            subject='[pyoperant notice] on rouse',
                                            credentials=None,
                                            secure=None)


logger = logging.getLogger()

smtp_handler.setLevel(logging.WARNING)

heading = '%s/Box %s\n' % ('test', '7')
formatter = logging.Formatter(heading + '%(levelname)s at %(asctime)s:\n%(message)s')
smtp_handler.setFormatter(formatter)
logger.addHandler(smtp_handler)
try:
    raise Exception()
except Exception as e:
    logger.exception('Unhandled Exception')